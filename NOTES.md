# Developers' Note

In this document we make notes for the sanity of future developers (aka ourselves). 

## Interfacing with NERSC authentication

When installing on NERSC, we opt to use NERSC's authentication system and bypass 
all user management systems that are in this code repo. 

On the backend, NERSC provides the sign-in user's username (as a server-side environment variable callled "uid"),
so the backend (i.e. php code) can directly access this info to obtain sign-in information. 
We hence do not need to track sessions (we modified `getUIDFromSID` in `common.php.inc` to make this work). 

However, most of the database required an integer user ID. Hence, we map the username to user id 
using a 1-to-1 reversible mapping (see `username2uid` in `common.nersc.php.inc`), and use the user id
throughout the database. 

Becuase of this bypassing, we are not using the `seeds`, `sessions`, and `users` tables in the users database. 
We also do not use `login.php`, `signup.php`, and `usermanagement.php`. 

On the frontend, NERSC provides the [newt API](https://newt.nersc.gov/) which allows us checking sign-in information 
using ajax. Because of this, we can get rid of our own cookie entirely. 
When the sign-in information is needed on the frontend, instead of checking cookie, we directly check with newt
(see `checkSessionCookie` in `assets/common.js`). 

Sometimes we want to display usernames on the frontend, but since the database on teh backend only store user ids,
we have to convert the ids back to usernames. So an inverse mapping function in javascipt can be used for this purpose 
(`uid2username` in `assets/common.js`). 
