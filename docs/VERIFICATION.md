# How verification works

## What is anchored

For every issued version the issuer key calls

```solidity
anchorVersion(bytes32 passportIdHash, uint32 version, bytes32 pdfHash, bytes32 codeHash)
```

| Field | Value |
|---|---|
| `passportIdHash` | `keccak256("BTU-AI-2026-00042")` |
| `version` | 1, 2, 3 … The contract only accepts `latest + 1` |
| `pdfHash` | SHA-256 of the exact PDF bytes |
| `codeHash` | SHA-256 of the 12-character verification code |

The contract also stores `issuedAt` (block time), `revokedAt` and `issuer` (`msg.sender`).
No names or personal data go on chain.

The verification code and QR are printed into the PDF **before** hashing; the hash is anchored
after. The PDF therefore never needs to contain its own hash.

## Two things are confirmed

**Document authenticity**
1. The version exists on chain.
2. The on-chain `pdfHash` equals the SHA-256 of the issued PDF (and of the file the verifier drops,
   computed in the browser).
3. The on-chain `codeHash` matches the code that was entered.
4. The version is not revoked.

**Issuer authenticity**
1. The address that anchored the version is authorised by the registry (`isIssuer`).
2. That address is listed by BTU at `https://<passport-domain>/.well-known/btu-issuer.json`
   and on the *Issuer identity* page.
3. The university register and the chain agree on the latest version.

Each PDF additionally contains an EIP-712 signature in its document properties (Keywords field),
over `(passportIdHash, version, codeHash, issuedAt)`, with domain
`{name: "BTU AI Skills Digital Passport", version: "1", chainId, verifyingContract}`.
Recovering the signer gives the issuer address even without network access.

## Statuses

| Status | Meaning |
|---|---|
| `valid_latest` | Authentic and the newest valid version |
| `valid_superseded` | Authentic, but a newer version exists |
| `revoked` | Withdrawn by BTU |
| `invalid` | Record and chain disagree, or issuer not confirmed |
| `not_found` | No passport with this code / hash |
| `pending` | Issued seconds ago, waiting for the block |
| `chain_unavailable` | Register found it, chain could not be reached right now |

## Independent check with Foundry's `cast`

```bash
sha256sum BTU-AI-2026-00001-v1.pdf
cast call <contract> "lookupPdf(bytes32)(bytes32,uint32,(bytes32,bytes32,uint64,uint64,address))" \
     0x<sha256> --rpc-url <rpc>
cast call <contract> "isIssuer(address)(bool)" <issuer-from-record> --rpc-url <rpc>
curl https://<passport-domain>/.well-known/btu-issuer.json
```
