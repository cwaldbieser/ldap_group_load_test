====================
LDAP Group Load Test
====================

A simple LDAP group load test.
Adds a member to a group and removes the member from the same group.
Will repeat as many times as indicated.

Requests occur over a single connection.
No LDAP SEARCH requests are made-- DNs are assumed to be known for the account and group entries ahead of time.
Assumes that account and group entries must be updated independently.

