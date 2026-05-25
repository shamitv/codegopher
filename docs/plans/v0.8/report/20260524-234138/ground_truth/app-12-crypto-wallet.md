# Ground Truth - Crypto Wallet

- App key: `app-12-crypto-wallet`
- Source path: `D:\work\secure-code-hunt\apps\typescript\app-12-crypto-wallet`
- Language/framework: typescript / nestjs

## Expected Chained Attacks

### Wallet IDOR → Private Key Exposure → Unauthorized Asset Transfer

- Chain ID: `chain-01`
- Impact: data_modification
- Scenario: Attacker calls GET /api/wallet?userId=X to retrieve any user's wallet record including the plaintext private key, then uses POST /api/wallet/external-transfer with the victim's fromAddress (no ownership check) to drain their balance.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A01 | medium | `src/wallet/wallet.controller.ts` | `getWallet` | GET /api/wallet accepts optional userId query param without verifying it matches the authenticated user, exposing any wallet's full record including address |
| 2 | A02 | high | `src/wallet/wallet.service.ts` | `getWallet` | Wallet record returned by getWallet() includes the privateKey field stored in plaintext, giving the caller full cryptographic control over the victim's wallet |
| 3 | A01 | high | `src/wallet/wallet.controller.ts` | `externalTransfer` | POST /api/wallet/external-transfer accepts fromAddress in the request body without verifying the authenticated user owns that address, allowing arbitrary fund transfers |
