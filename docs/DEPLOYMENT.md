# Deployment

## Any Linux VPS with Docker

```bash
git clone <repo> && cd AI_Skills_Digital_Passport
cp .env.example .env    # then edit as below
mkdir -p docker/nginx/certs   # fullchain.pem + privkey.pem (e.g. from certbot)
docker compose --profile prod up -d --build
```

`.env` changes for production:

```bash
DJANGO_DEBUG=false
SECRET_KEY=<50+ random characters>
PUBLIC_BASE_URL=https://passport.btu.edu.ge
ALLOWED_HOSTS=passport.btu.edu.ge,web
CSRF_TRUSTED_ORIGINS=https://passport.btu.edu.ge
BEHIND_TLS_PROXY=true
SECURE_COOKIES=true
SEED_DEMO_ON_START=false
ADMIN_BOOTSTRAP_EMAILS=<passport office emails>
EMAIL_HOST=<smtp host>  EMAIL_PORT=587  EMAIL_USE_TLS=true  EMAIL_HOST_USER=…  EMAIL_HOST_PASSWORD=…
```

In production remove the `ports:` of `web`, `postgres`, `anvil`, `mailpit` (only nginx should be
exposed) and point `EMAIL_HOST` to real SMTP. Back up the `pgdata` and `media` volumes.

## Polygon Amoy testnet (or Polygon mainnet)

1. Create two keys: an **owner** (keep offline) and an **issuer** (used by the worker).
2. Fund both from https://faucet.polygon.technology (owner only needs gas for deploy + setIssuer).
3. `.env`:

```bash
CHAIN_RPC_URL=https://rpc-amoy.polygon.technology
CHAIN_ID=80002
CHAIN_NAME=Polygon Amoy testnet
AUTO_DEPLOY_CONTRACT=false
CHAIN_OWNER_PRIVATE_KEY=0x…
CHAIN_ISSUER_PRIVATE_KEY=0x…
EXPLORER_TX_URL=https://amoy.polygonscan.com/tx/{}
EXPLORER_ADDRESS_URL=https://amoy.polygonscan.com/address/{}
```

4. `docker compose up -d && docker compose exec web python manage.py deploy_contract`
   The address is recorded in the database and `chain/deployments/80002.json`.
   Optionally pin it with `CONTRACT_ADDRESS=` and remove `CHAIN_OWNER_PRIVATE_KEY` from the server.
5. Remove the `anvil` service from the compose file.

For mainnet use `CHAIN_ID=137`, a mainnet RPC and `https://polygonscan.com/tx/{}`.
Rotate the issuer later with `setIssuer(new, true)` then `setIssuer(old, false)` from the owner key;
old anchors stay verifiable because the record stores which address anchored them.
