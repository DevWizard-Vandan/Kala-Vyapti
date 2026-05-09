use pyo3::prelude::*;

pub mod clustering;
pub mod indicators;

/// Return a static greeting to verify the Python bindings are loaded.
#[pyfunction]
fn hello_world() -> &'static str {
    "Hello from Kala-Vyapti Rust core"
}

/// Python module for the Kala-Vyapti Rust signal engine.
#[pymodule]
fn kala_vyapti_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello_world, m)?)?;
    Ok(())
}
