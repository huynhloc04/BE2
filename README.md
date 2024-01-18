##  ***Install pdftotext***
### 1. Install pdftotext dependencies
### ***Debian, Ubuntu*** 
```bash
    sudo apt install build-essential libpoppler-cpp-dev pkg-config python3-dev
```


### ***Fedora, Red Hat*** 
```bash
    sudo yum install gcc-c++ pkgconfig poppler-cpp-devel python3-devel
```


### ***macOS*** 
```bash
    brew install pkg-config poppler python
```


### ***Windows*** 
```bash
    conda install -c conda-forge poppler
```


### 2. Install pdftotext
```bash
    pip install pdftotext
```