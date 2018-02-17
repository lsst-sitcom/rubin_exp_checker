# Developers' Note

In this document we make notes for the sanity of future developers (aka ourselves). 

## Interfacing with NERSC authentication

When installing on NERSC, we opt to use NERSC's authentication system and bypass 
all user management systems that are in this code repo. 

On the back end, NERSC provides the sign-in user's user name 
(as a server-side environment variable called `uid`, see `getUsername` in `common.nersc.php.inc`),
so the back end (i.e. php code) can directly access this variable to obtain sign-in information. 
We hence do not need to track sessions (we modified `getUIDFromSID` in `common.php.inc` to make this work). 

However, most of the database required an integer user id. 
Hence, we map the user name to an integer id using a 1-to-1 reversible mapping 
(see `username2uid` in `common.nersc.php.inc`), and use the user id throughout the database. 

Because of this bypassing strategy, we are not using the `seeds`, `sessions`, and `users` tables in the users database. 
We also do not use `login.php`, `signup.php`, and `usermanagement.php` on the back end. 

On the front end, NERSC provides the [newt API](https://newt.nersc.gov/), 
which allows us to obtain sign-in information using ajax. 
Hence, we can get rid of our own cookie entirely. 
When the sign-in information is needed on the front end, 
instead of checking cookie, we directly check with newt
(see `checkSessionCookie` in `assets/common.js`). 

In many cases we want to display user names on the front end, 
but the databases on the back end only store user ids.
Original code uses the `users` table to obtain user names from user ids; 
however, we are not using the `users` table anymore.
So we let the back end just return user id, 
and implemented an inverse mapping function on the front end to convert user ids back
to user names (see `uid2username` in `assets/common.js`). 
