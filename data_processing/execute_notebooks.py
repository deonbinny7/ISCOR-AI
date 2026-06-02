from pathlib import Path

import nbformat
from nbclient import NotebookClient


NOTEBOOKS = [
    Path("notebooks/Part1_EDA.ipynb"),
    Path("notebooks/Part3_SHAP_Analysis.ipynb"),
]


def execute_notebook(path: Path, timeout: int = 300) -> None:
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
    )
    client.execute()
    nbformat.write(notebook, path)
    print(f"Executed {path}")


if __name__ == "__main__":
    for notebook_path in NOTEBOOKS:
        execute_notebook(notebook_path)
