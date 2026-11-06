# <Product>: constraints

What the product has to work within. A table row starts with an anchor named after its name, so a requirement can link to it: `<a id="quote-latency"></a>Quote latency` is reached by `[Quote latency](constraints.md#quote-latency)`. A constraint that needs more than a row has a heading instead: `## Quote latency` is reached the same way.

## Services it calls

| Service | What for | API |
|---|---|---|

## Client software that will call it

| Client | What for | API |
|---|---|---|

## Data it will own

| Data | Where it comes from |
|---|---|

## Limits

Regulatory, security and performance limits. Every number is a target, recorded with who set it and why. Each target becomes a non-functional requirement in `requirements.md`, on the state or transition where the user feels it, and that requirement links back here. A limit with no number leaves *Target* empty.

| Limit | Kind | Target | Set by | Why |
|---|---|---|---|---|
