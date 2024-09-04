from cx_Freeze import setup, Executable

setup(
    name = "InstaBulkCommenter",
    version = "1.0",
    description = "Bulk Instagram Commenter Tool",
    executables = [Executable("main.py")]
)
