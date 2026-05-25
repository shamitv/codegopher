# Ground Truth - app-12-crypto-wallet

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

### Subtle Auth Session Pivot To Crypto

- Chain ID: `chain-02`
- Impact: data_modification
- Scenario: Attacker combines a low-visibility entry point with stored or derived application state, then pivots to a higher-impact sink that is reachable only after following the cross-file flow.

| Step | OWASP | Severity | Location | Method | Description |
|---|---|---|---|---|---|
| 1 | A07 | high | `src/wallet/wallet.service.ts` | `executeTransfer` | Identification and Authentication Failures. High-value transactions (transfers of any amount) are processed without requiring Multi-Factor Authentication (MFA) or step-up authentication. |
| 2 | A04 | high | `src/wallet/wallet.controller.ts` | `transferFunds` | Insecure Design. The transfer funds endpoint executes immediately upon request without any transaction confirmation step, multi-step validation, or intent verification. |
| 3 | A02 | critical | `src/wallet/wallet.service.ts` | `createWallet` | Cryptographic Failures. Wallet private keys are stored in the database in plaintext without any encryption or secure enclave protection. |
