@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

set SPHINXOPTS=
set SOURCEDIR=.
set BUILDDIR=_build

REM Check if sphinx-build is available
where sphinx-build >NUL 2>NUL
if errorlevel 1 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed. Install it with: pip install -r requirements-docs.txt
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://sphinx-doc.org/
	exit /b 1
)

if "%1" == "" (
	sphinx-build -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%
) else (
	sphinx-build -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%
)

popd

