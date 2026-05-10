use crate::indicators::{supertrend, Candle};

/// SuperTrend AI output selected by k-means clustering over factor performance.
#[derive(Debug, Clone, PartialEq)]
pub struct SuperTrendAiResult {
    pub trend: Vec<i8>,
    pub upper: Vec<f64>,
    pub lower: Vec<f64>,
    pub selected_factor: f64,
    pub cluster_perfs: [f64; 3],
}

/// Select a SuperTrend multiplier by clustering factor performance into worst,
/// average, and best groups, then return the final SuperTrend for that factor.
pub fn supertrend_ai(
    candles: &[Candle],
    atr_period: usize,
    min_mult: f64,
    max_mult: f64,
    step: f64,
    perf_alpha: f64,
    from_cluster: usize,
) -> SuperTrendAiResult {
    let factors = generate_factors(min_mult, max_mult, step);

    if candles.is_empty() || factors.is_empty() {
        return SuperTrendAiResult {
            trend: vec![0; candles.len()],
            upper: vec![f64::NAN; candles.len()],
            lower: vec![f64::NAN; candles.len()],
            selected_factor: f64::NAN,
            cluster_perfs: [f64::NAN; 3],
        };
    }

    let alpha = 2.0 / (perf_alpha + 1.0);
    let mut factor_perfs = Vec::with_capacity(factors.len());

    for factor in &factors {
        let (trend, upper, lower) = supertrend(candles, atr_period, *factor);
        let mut perf = 0.0;

        for i in 1..candles.len() {
            let output = supertrend_output(trend[i - 1], upper[i - 1], lower[i - 1]);
            let direction = if output.is_nan() {
                0.0
            } else {
                (candles[i - 1].close - output).signum()
            };
            let price_change = candles[i].close - candles[i - 1].close;
            perf += alpha * (price_change * direction - perf);
        }

        factor_perfs.push((*factor, perf));
    }

    let clusters = kmeans_three_clusters(&factor_perfs);
    let target_cluster = from_cluster.min(2);
    let selected_factor = average_factor(&clusters[target_cluster]).unwrap_or_else(|| {
        nearest_factor_to_centroid(&factor_perfs, clusters[target_cluster].centroid)
    });

    let (trend, upper, lower) = supertrend(candles, atr_period, selected_factor);

    SuperTrendAiResult {
        trend,
        upper,
        lower,
        selected_factor,
        cluster_perfs: [
            clusters[0].centroid,
            clusters[1].centroid,
            clusters[2].centroid,
        ],
    }
}

#[derive(Debug, Clone)]
struct Cluster {
    centroid: f64,
    members: Vec<(f64, f64)>,
}

fn generate_factors(min_mult: f64, max_mult: f64, step: f64) -> Vec<f64> {
    if !min_mult.is_finite() || !max_mult.is_finite() || !step.is_finite() || step <= 0.0 {
        return Vec::new();
    }

    let mut factors = Vec::new();
    let mut factor = min_mult;
    let epsilon = step.abs() * 1e-9;

    while factor <= max_mult + epsilon {
        factors.push(factor);
        factor += step;
    }

    factors
}

fn supertrend_output(trend: i8, upper: f64, lower: f64) -> f64 {
    if trend == 1 {
        lower
    } else if trend == -1 {
        upper
    } else {
        f64::NAN
    }
}

fn kmeans_three_clusters(factor_perfs: &[(f64, f64)]) -> [Cluster; 3] {
    let perf_values: Vec<f64> = factor_perfs
        .iter()
        .map(|(_, perf)| *perf)
        .filter(|perf| perf.is_finite())
        .collect();

    if perf_values.is_empty() {
        return [
            Cluster {
                centroid: 0.0,
                members: Vec::new(),
            },
            Cluster {
                centroid: 0.0,
                members: Vec::new(),
            },
            Cluster {
                centroid: 0.0,
                members: Vec::new(),
            },
        ];
    }

    let mut centroids = [
        percentile(&perf_values, 25.0),
        percentile(&perf_values, 50.0),
        percentile(&perf_values, 75.0),
    ];
    let mut clusters = empty_clusters(centroids);

    for _ in 0..1000 {
        clusters = empty_clusters(centroids);

        for &(factor, perf) in factor_perfs {
            let nearest = nearest_centroid(perf, &centroids);
            clusters[nearest].members.push((factor, perf));
        }

        let mut next_centroids = centroids;
        for index in 0..3 {
            if !clusters[index].members.is_empty() {
                let sum: f64 = clusters[index].members.iter().map(|(_, perf)| *perf).sum();
                next_centroids[index] = sum / clusters[index].members.len() as f64;
            }
            clusters[index].centroid = next_centroids[index];
        }

        if centroids_converged(&centroids, &next_centroids) {
            break;
        }

        centroids = next_centroids;
    }

    clusters.sort_by(|left, right| left.centroid.total_cmp(&right.centroid));
    clusters
}

fn empty_clusters(centroids: [f64; 3]) -> [Cluster; 3] {
    [
        Cluster {
            centroid: centroids[0],
            members: Vec::new(),
        },
        Cluster {
            centroid: centroids[1],
            members: Vec::new(),
        },
        Cluster {
            centroid: centroids[2],
            members: Vec::new(),
        },
    ]
}

fn percentile(values: &[f64], percentile: f64) -> f64 {
    let mut sorted = values.to_vec();
    sorted.sort_by(|left, right| left.total_cmp(right));

    if sorted.len() == 1 {
        return sorted[0];
    }

    let rank = (percentile / 100.0) * (sorted.len() - 1) as f64;
    let lower = rank.floor() as usize;
    let upper = rank.ceil() as usize;

    if lower == upper {
        sorted[lower]
    } else {
        let weight = rank - lower as f64;
        sorted[lower] + (sorted[upper] - sorted[lower]) * weight
    }
}

fn nearest_centroid(value: f64, centroids: &[f64; 3]) -> usize {
    let mut nearest = 0;
    let mut nearest_distance = (value - centroids[0]).abs();

    for (index, centroid) in centroids.iter().enumerate().skip(1) {
        let distance = (value - centroid).abs();
        if distance < nearest_distance {
            nearest = index;
            nearest_distance = distance;
        }
    }

    nearest
}

fn centroids_converged(current: &[f64; 3], next: &[f64; 3]) -> bool {
    current
        .iter()
        .zip(next.iter())
        .all(|(left, right)| (*left - *right).abs() < 1e-12)
}

fn average_factor(cluster: &Cluster) -> Option<f64> {
    if cluster.members.is_empty() {
        return None;
    }

    let sum: f64 = cluster.members.iter().map(|(factor, _)| *factor).sum();
    Some(sum / cluster.members.len() as f64)
}

fn nearest_factor_to_centroid(factor_perfs: &[(f64, f64)], centroid: f64) -> f64 {
    factor_perfs
        .iter()
        .min_by(|(_, left_perf), (_, right_perf)| {
            (left_perf - centroid)
                .abs()
                .total_cmp(&(right_perf - centroid).abs())
        })
        .map(|(factor, _)| *factor)
        .unwrap_or(f64::NAN)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn trending_candles() -> Vec<Candle> {
        (0..100)
            .map(|i| {
                let close = 100.0 + i as f64 * 0.75;
                Candle {
                    open: close - 0.3,
                    high: close + 1.0,
                    low: close - 1.0,
                    close,
                    volume: 1000.0 + i as f64,
                }
            })
            .collect()
    }

    #[test]
    fn clusters_supertrend_factors_for_trending_data() {
        let candles = trending_candles();
        let result = supertrend_ai(&candles, 10, 1.0, 5.0, 0.5, 10.0, 2);

        assert!(result.selected_factor >= 1.0);
        assert!(result.selected_factor <= 5.0);
        assert_eq!(result.trend.len(), candles.len());
        assert!(result.cluster_perfs[2] >= result.cluster_perfs[1]);
        assert!(result.cluster_perfs[1] >= result.cluster_perfs[0]);
    }
}
