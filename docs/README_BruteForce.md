
# Brute Force
## Description
*Note: In order to attempt the attack, an assumption is made that the attacker already knows the Administrator's email address:* admin@example.com *.*

*The email address can be retrieved by entering the URL* http://127.0.0.1:8080/admin *(Authorization Bypass), and then inputting the following command into the user id input box (Error-Based SQL Injection):*

`' or ExtractValue(1, concat(':', (SELECT email FROM users WHERE role='admin' LIMIT 1))) or '`

*See Authorization Bypass and Error-Based SQL Injection for more information on these attacks.*

This attack repeatedly enters one or more inputs until a successful login is found. In this case, the program BurpSuite is used to enter a known email, followed by a list of commonly used - and therefore insecure - passwords.

 1. Open BurpSuite, click 'Next' and 'Start Burp'. If a pop-up saying "BurpSuite is out of date" appears, click 'OK' (the version available in the Kali Linux distribution is acceptable for this attack).
![Alt text](./screenshots/BruteForce/BruteForceDesc1-1.png)
![Alt text](./screenshots/BruteForce/BruteForceDesc1-2.png)
![Alt text](./screenshots/BruteForce/BruteForceDesc1-3.png)
 2. Click the 'Open pre-configured browser' button in the top-right corner of BurpSuite, head to the Login page (http://127.0.0.1:8080/login).
 ![Alt text](./screenshots/BruteForce/BruteForceDesc2-1.png)
 ![Alt text](./screenshots/BruteForce/BruteForceDesc2-2.png)
 3. Click on the 'Proxy' tab on BurpSuite, then 'Intercept off' to turn on Intercept; this will intercept any HTTP requests such as GET or POST, which will occur when switching to a different page, clicking buttons, or submitting information in the input boxes.
 ![Alt text](./screenshots/BruteForce/BruteForceDesc3-1.png)
 ![Alt text](./screenshots/BruteForce/BruteForceDesc3-2.png)
 ![Alt text](./screenshots/BruteForce/BruteForceDesc3-3.png)
 4. Enter admin@example.com and a random password ("pass" is used in this example), then click 'Sign In'. BurpSuite will intercept this submission. Right-click the interception, then click 'Send to Intruder'.
  ![Alt text](./screenshots/BruteForce/BruteForceDesc4-1.png)
  ![Alt text](./screenshots/BruteForce/BruteForceDesc4-2.png)
 5. Click on the 'Intruder' tab, delete the word "pass" from Line 22, then click 'Add §'. This should add "§§" next to the line "email=admin%40example.com&password=".
 ![Alt text](./screenshots/BruteForce/BruteForceDesc5-1.png)
  ![Alt text](./screenshots/BruteForce/BruteForceDesc5-2.png)
   ![Alt text](./screenshots/BruteForce/BruteForceDesc5-3.png)
    ![Alt text](./screenshots/BruteForce/BruteForceDesc5-4.png)
 6. Under 'Payload configuration', click 'Load...', select the rockyou.txt wordlist and click 'Open'. This can be found in the Kali Linux distribution in the path /usr/share/wordlists, although the file can also be found [here](https://github.com/RykerWilder/rockyou.txt).
*Note: The file is very large, so opening the file may take a few seconds.*
  ![Alt text](./screenshots/BruteForce/BruteForceDesc6-1.png)
    ![Alt text](./screenshots/BruteForce/BruteForceDesc6-2.png)
      ![Alt text](./screenshots/BruteForce/BruteForceDesc6-3.png)
 7. Click 'Start attack'. After a few minutes, a pop-up message saying "Burp Intruder: The Community Edition of Burp Suite contains a demo version of Burp Intruder...". Click 'OK'.
  ![Alt text](./screenshots/BruteForce/BruteForceDesc7-1.png)
## Result
A page featuring the many attacks performed is shown in the form of requests. Clicking on the column header 'Status Code' will reveal the request "password" with a status code of 302 (a [HTTP 302 Found redirection response](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/302)) and a length significantly shorter then the other requests listed. This indicates that the correct password is found.
 ![Alt text](./screenshots/BruteForce/BruteForceRes1.png)
Entering this password with the email address should successfully log in to the Admin Account and redirect to the Admin's Database page.
 ![Alt text](./screenshots/BruteForce/BruteForceRes2.png)
  ![Alt text](./screenshots/BruteForce/BruteForceRes3.png)

## Code Vulnerability
The login authorization checks if the user and password match; if they do not match, the error message "Invalid email or password." appears:
```python
# Validate password if user exists
if user and user.check_password(password):
    session["user_id"] = user.id
    session["user_fname"] = user.first_name
    if user.role == UserRole.ADMIN:
        return redirect(url_for("admin.admin"))
    else:
        return redirect(url_for("account.accounts"))

return render_template("login.html", error="Invalid email or password."), 401
```
However, there is no penalty for performing unsuccessful logins multiple times. Because of this, a program like BurpSuite can input multiple passwords consecutively until a match is found.

## Code Improvement
The code was modified to include a lockout if 3 or more login attempts occur.

If a unsuccessful login is performed, a counter for total_failed_logins is incremented by 1. If the counter reaches 3 or more failed attempts, the user_lockout is set to True, and the error message "Too many failed login attempts. The account is now locked." appears.

```python
            if security_choice == "hardened":
                # Unsuccessful login = increment total_failed_logins
                user.total_failed_logins += 1
                if user.total_failed_logins >= 3:
                    user.user_lockout = True
                db.session.commit()
```
All subsequent login attempts will show this error message.
```python
        # Check user is lockedout before checking password
        if security_choice == "hardened" and user.user_lockout:
            # Permanent lockout
            return (
                render_template(
                    "login.html",
                    error="Too many failed login attempts. The account is now locked.",
                    security_choice="hardened",
                    locked=user.user_lockout,
                ),
                429,
            )
```
Finally, for educational purposes a "Reset Lockout" button is also included to allow the user to reset the email address that was locked, so they can test the vulnerable/hardened code again.
```python
def reset_lockout():
    # Reset lockout for account/email
    email = request.form.get("email")

    # Missing email
    if not email:
        return (
            render_template(
                "login.html",
                error="Please enter a valid email.",
                security_choice="hardened",
                locked=True,
            ),
            400,
        )

    user = db.session.scalars(db.select(User).where(User.email == email)).first()

    # Invalid email
    if not user:
        return (
            render_template(
                "login.html",
                error="Please enter a valid email.",
                security_choice="hardened",
                locked=True,
            ),
            400,
        )

    # Reset lockout
    user.user_lockout = False
    user.total_failed_logins = 0
    db.session.commit()
```

## Retesting Result
Now when the email and an incorrect password is submitted 3 times, the message "Too many failed login attempts. The account is now locked. appears. Even if the correct password is inputted during the lockout, the user cannot log in unless the "Reset Lockout" button is used.
 ![Alt text](./screenshots/BruteForce/BruteForceRetest1.png)