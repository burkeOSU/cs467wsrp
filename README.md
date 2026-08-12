# CS 467: Website Security Research Project
Fern Burke and Mary Dean
## Description
The basic web application is centered around users being able to register and then store information about their bank accounts (name, account number, and balance).  As the users navigate through the site, they encounter toggle buttons with “Vulnerable” and “Hardened” options.  This indicates that there is an attack option available on that page.  Vulnerable mode allows the attack to happen, whereas Hardened mode prevents the attack.  On some pages, the security mode is selected with a form submission.  On other pages, the security mode is its own separate form, updating a session variable on submit.  This should be fairly intuitive for the user, as there is only one toggle per page.  

Additionally, there are hint buttons at the bottom of the pages with attack options.  The “Attack Hint” button displays the name of the attack and instructions for performing it.  The “Explanation” button provides a link to the attack’s associated README on the public GitHub repository, which provides details about the attack, the code vulnerability that allowed it, and the code implementation to protect against the attack.

After navigating through all of the pages on the site, the user should have encountered seven different attack opportunities. Additionally, if the README links were followed, the user should have a reasonable understanding of the attack along with the code vulnerability and protection.
## Installation
### Oracle VirtualBox and Kali Linux (Optional)
While installing a virtual machine and distribution is not necessary to run the web application and perform every attack documented, it may be useful when performing penetration testing, particularly attacks like Brute Force which require repetitive inputting. Kali Linux was specifically designed for penetration testing and ethical hacking, and as such comes with pre-installed tools and documents such as payload text files containing commonly used/insecure password lists. Installation onto a virtual machine is recommended to prevent erroneous terminal commands from irreversibly damaging the user’s OS, and a Kali Linux pre-built image is available for Oracle VirtualBox in particular, hence why this specific virtual machine is used in the instructions below:

1. Go to https://www.virtualbox.org/wiki/Downloads and select the Platform Package which matches the user’s OS.
2. Accept the license agreement and use the default features to install.
3. Then go to https://www.kali.org/get-kali/#kali-virtual-machines and select the VirtualBox image for download.
4. In the Oracle VirtualBox Manager, select “Open” followed by the downloaded Kali Linux image.
5. The default user credentials for the distribution are:

User Name: kali
Password: kali

6. Once logged in, both the Deployed and Local Installation instructions can be followed below to access the web application.
### Web Application
Deployed Application
https://cs467-wsrp-burke-dean.uc.r.appspot.com/
### Local Installation 
These instructions assume you have git, Python, and MySQL installed on your computer and are specific to Mac OS or Linux.

Create a new directory on which you want to install the project.  Then, clone down the repo for the project:

`git clone https://github.com/burkeOSU/cs467wsrp.git`

Then, create a virtual Python environment within the current directory and activate it:

`python -m venv env
source env/bin/activate`

Click here for more details including Windows specific instructions. 

Afterward, run the following to install the project dependencies in the virtual environment:

`pip install -r requirements.txt`

Next, you’ll need to create a local instance of a MySQL database to connect to the project.  You should also create a new user for the project.  This can be done with the following commands after starting the local MySQL server:

`mysql -u root -p
CREATE DATABASE project_db;
CREATE USER 'project_user'@'localhost' IDENTIFIED BY 'a_password';
GRANT ALL PRIVILEGES ON project_db.* TO 'project_user'@'localhost';`

Then, create a .env in the root directory of the project.  You will use this file to store the database credentials you just created, as well as a project secret key that should be a secure random string that you generate.
 

Finally, in the project directory with the Python virtual environment activated, run the following command to start up the app:

`python app.py`
