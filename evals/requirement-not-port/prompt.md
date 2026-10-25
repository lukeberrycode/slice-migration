---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

We're replacing a legacy Java EE trading app (IBM DayTrader 8) with a new Python slice. We're in the Discovery phase: drawing requirements from the legacy code and confirming them with characterisation tests against the running legacy app. The legacy code is in `legacy/daytrader8`; Discovery documents are in `docs/discovery/`.

Here is the method that registers a user in the legacy app, simplified:

```java
public AccountDataBean register(String userID, String password, String fullname, String address,
    String email, String creditcard, BigDecimal openBalance) {
  AccountProfileDataBean profile = entityManager.find(AccountProfileDataBean.class, userID);
  if (profile != null) throw new EJBException("User " + userID + " already exists");
  profile = new AccountProfileDataBean(userID, password, fullname, address, email, creditcard);
  AccountDataBean account = new AccountDataBean(0, 0, null, new Timestamp(System.currentTimeMillis()), openBalance, openBalance, userID);
  profile.setAccount(account);
  account.setProfile(profile);
  entityManager.persist(profile);
  entityManager.persist(account);
  return account;
}
```

Write the requirements for registration that the new Python slice must meet.
