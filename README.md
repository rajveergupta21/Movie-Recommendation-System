# Python Virtual Environment and Required Modules

This project uses a Python virtual environment to manage dependencies and a CSV dataset. You can place the CSV file in the project root or provide a Google Drive link to access the data.

**Download the dataset:**  
https://drive.google.com/file/d/1a8aFD9HdfI_SiktIenLJv63YwFPZ5CUI/view?usp=sharing

## Using the dataset
Download the dataset from the link above and place it in the project root directory alongside your `movie_recommender.py` file.


### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### On Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

## Upgrading pip

After activating the virtual environment, upgrade pip to the latest version:
```bash
pip install --upgrade pip
```

## Installing Required Modules

Install the required Python modules one by one using pip:
```bash
pip install flask
pip install pandas
pip install python-dotenv
```