import { Faucet } from "../contracts/faucet/index.js";
import { parseUtxo } from "../utils/transaction.js";

/**
 * @param {Object} contractOpts
 */
export function compileFaucetContract(contractOpts) {
  const faucet = new Faucet(contractOpts);
  const contract = faucet.getContract();
  return { address: contract.address, tokenAddress: contract.tokenAddress }
}

/**
 * @param {Object} opts
 * @param {Object} opts.contractOpts
 * @param {import("cashscript").Utxo} opts.utxo
 * @param {String} opts.recipient
 * @param {String} opts.passcode
 * @param {Number} [opts.locktime]
 */
export async function faucetClaim(opts) {
  const faucet = new Faucet(opts?.contractOpts);

  const { error, transaction } = faucet.claim({
    utxo: parseUtxo(opts?.utxo),
    recipient: opts?.recipient,
    passcode: opts?.passcode,
    locktime: opts?.locktime,
  })

  if (error) return { success: false, error }
  return { success: true, transaction: await transaction.build() }
}


/**
 * @param {Object} opts
 * @param {Object} opts.contractOpts
 * @param {String} opts.wif
 * @param {import("cashscript").Utxo[]} opts.utxos
 * @param {String} [opts.recipient]
 * @param {Number} [opts.locktime]
 */
export async function faucetSweep(opts) {
  const faucet = new Faucet(opts?.contractOpts);
  const { error, transaction } = faucet.faucetSweep({
    wif: opts?.wif,
    utxos: opts.utxos.map(parseUtxo),
    recipient: opts?.recipient || faucet.params.ownerAddress,
    locktime: opts.locktime,
  }); 

  if (error) return { success: false, error }
  return { success: true, transaction: await transaction.build() }
}
