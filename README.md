# Automated Housing Application

As we know that in some big cities finding a home is getting Difficutly day by day. In order to reduce the difficulty I have written an automated form submission script using Selenium WebDriver. It reads user details and form URLs from separate JSON files and submits the form for each user on each URL. With the help of this script I have started to get Viewing invitations for almost every apartment I have applied to. I have created several email adresses and with those adresses I have let the code aplly for me. In Berlin, where I currently leave, Average Apartments get around 800 Applications only in one hour. Considering this, I belive that this is a big Accomplishment for me. **Due to Data Privacy I can not write here at what website the code is working**.


## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Configuration](#configuration)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

- Python 3.x
- Selenium
- Firefox WebDriver (geckodriver)

## Installation

1. **Clone the repository**:
 ```sh
 git clone https://github.com/your-username/automated-form-submission.git
 cd automated-form-submission 
``` 
2. **Install dependencies**:
```sh
pip install selenium
```
3. **Download and install geckodriver**:
- Download the appropriate version of geckodriver for your operating system from the [geckodriver releases page](https://github.com/mozilla/geckodriver/releases).
- Extract the downloaded file and add the directory to your system's PATH.

## Project Structure
```sh
automated-Housing-Application/
│
├── user_details.json      # JSON file containing user details
├── links.json             # JSON file containing form URLs
├── form_submitter.py      # Main Python script to submit the form
└── README.md              # Project documentation
```

## Usage
1. **Prepare the Json Files**:
   - Create a `user_details.json` file with user details. You can add as many user as you want:
```json
[
    {
        "email": "your Email adress1",
        "first_name": "Name1",
        "surname": "Surname1",
        "phone_number": "+4998327492",
        "street": "Randomstreet",
        "house_number": " ",
        "postal_code": " ",
        "city": "Jupiter",
        "total_persons": "4"
    },
    {
        "email": "your Email adress2",
        "first_name": "Name2",
        "surname": "Surname2",
        "phone_number": "+499833427492",
        "street": "Randomstreet2",
        "house_number": " ",
        "postal_code": " ",
        "city": "Jupiter",
        "total_persons": "4"
    },
]
```
   - Create a `links.json` file with the form URLs. You can add as many URL as you need:
```json
[
    "randomlink1.com",
    "randomlink2.com"
]
```
2. **Run the Script**:
```Python
python form_submitter.py
```

## Configuration
- **user_details.json**: Contains the user details that will be filled in the form.
- **links.json**: Contains the URLs of the forms to be submitted.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


