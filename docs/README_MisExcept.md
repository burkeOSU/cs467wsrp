# Mishandled Exception
## Description
This attack purposefully triggers an error that causes an exception to be raised.
Often developers will implement a custom 500 error page to appear more professional
than the standard Flask template. Sometimes, error messages are hidden in these
templates for debugging purposes. However, these should be removed as an attacker
could intentionally trigger these error pages to check for encoded error details.

This is submitted as the first name input:
`Ex', 'Ample', 'pass', 1); #`

![Mishandled Exception before attack](./screenshots/MisExc/MisExcBefore.png)
## Result
The input generates an error, since it does not align correctly with the table
attributes. The generic handler function for 500 status codes is triggered, rendering
a custom 500 error page and including the error message in a comment in the html page,
which can be viewed on inspection.
From this, the attacker can learn the correct sequence of values to insert into the database, and
that the default user role is 'customer'. Then, the attacker could infer that 'admin'
is another role type, and use that to set up an admin account. Using the following text
as the first name input in vulnerable mode does indeed create an admin account:

`Ex', 'Ample', 'admin', 'pass'); #`

![Mishandled Exception after attack](./screenshots/MisExc/MisExcResult.png)
## Code Vulnerability
The vulnerability lies within the route function, which executes assuming no
errors can take place when creating the new user and saving it to the database.

```python
    # Insecure stmt that allows for SQL injection
    stmt = (
        "INSERT INTO users (email, first_name, last_name, role, "
        "password_hash)"
        f"VALUES ('{email}', '{first_name}', '{last_name}', '{role}', "
        f"'{password_hash}')"
    )

    # Insecure code, not in try/except block
    result = db.session.execute(text(stmt))
    db.session.commit()
    # Retrieve newly created user info to set session variables
    new_user_id = result.lastrowid
    user = db.session.get(User, new_user_id)
    session["user_id"] = user.id
    session["user_fname"] = user.first_name
    return redirect(url_for("account.accounts"))
```

Also, an error should be handled gracefully and not trigger the default 500 error page.
If it does, error messages should not be included in the 500 error page template. Despite
this making debugging easier in production, it introduces a vulnerability, as an attacker
can also gain information from it.

```python
@app.errorhandler(500)
def handle_exception(e):
    detailed_error = getattr(e, "original_exception", e)

    return render_template("error_500.html", error_message=str(detailed_error)), 500
```

## Code Improvement
The register code should be placed in a try/except block. That way, any errors
triggered by saving to the database are caught and properly handled,
without revealing sensitive information about the database.

```python
# Insecure stmt that allows for SQL injection
stmt = (
    "INSERT INTO users (email, first_name, last_name, role, "
    "password_hash)"
    f"VALUES ('{email}', '{first_name}', '{last_name}', '{role}', "
    f"'{password_hash}')"
)
# Try/except block to gracefully handle any exceptions
try:
    # Send constructed stmt to database to register user
    result = db.session.execute(text(stmt))
    db.session.commit()
    # Retrieve newly created user info to set session variables
    new_user_id = result.lastrowid
    user = db.session.get(User, new_user_id)
    session["user_id"] = user.id
    session["user_fname"] = user.first_name
    return redirect(url_for("account.accounts"))
except BaseException:
    db.session.rollback()
    # Appropriate generic error message is displayed back to user
    return render_template(
        "register.html",
        error="An error occurred creating the new user.",
        security="hardened",
    ), 500
```
Additionally, the error handler function for 500 status code should render
without including the error message in the comments to protect the app in
production.

```python
@app.errorhandler(500)
def handle_exception(e):
    return render_template("error_500.html"), 500
```

## Retesting Result
Now, when an error occurs trying to register the new user, it is caught with 
an appropriate error message displayed.

![Mishandled Exception retest result](./screenshots/MisExc/MisExcFixed.png)
