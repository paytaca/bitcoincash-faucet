import { hexToBin, opInputSequenceNumber, utf8ToBin } from "@bitauth/libauth"
import { compileFile } from "cashc"
import { Contract, ElectrumNetworkProvider, SignatureTemplate } from "cashscript"
import { addressToPkHash, toTokenAddress } from "../../utils/crypto.js"
import { calculateInputSize } from "../../utils/transaction.js"
import { getTxSizeWithoutInputs } from "cashscript/dist/utils.js"

export class Faucet {
  /**
   * @param {Object} opts
   * @param {Object} opts.params
   * @param {String} opts.params.passcode
   * @param {Number} opts.params.payoutSats
   * @param {String} opts.params.ownerAddress
   * @param {Object} opts.options
   * @param {'mainnet' | 'chipnet'} opts.options.network
   */
  constructor(opts) {
    this.params = {
      passcode: opts?.params?.passcode,
      payoutSats: opts?.params?.payoutSats,
      ownerAddress: opts?.params?.ownerAddress,
    }

    this.options = {
      network: opts?.options?.network,
    }
  }

  get contractParams() {
    return [
      BigInt(this.params.payoutSats),
      hexToBin(addressToPkHash(this.params.ownerAddress)),
      utf8ToBin(this.params.passcode),
    ]
  }

  get claimTxFee() {
    return 300n;
  }

  getContract() {
    // const provider = new ElectrumNetworkProvider('testnet4');
    const provider = new ElectrumNetworkProvider(this.options.network);
    const addressType = 'p2sh32';
    const opts = { provider, addressType, }

    const cashscriptFilename = 'faucet.cash'
    const artifact = compileFile(new URL(cashscriptFilename, import.meta.url));
    const contract = new Contract(artifact, this.contractParams, opts);

    return contract
  }

  /**
   * @param {Object} opts
   * @param {import("cashscript").Utxo} opts.utxo
   * @param {String} opts.recipient
   * @param {String} opts.passcode
   * @param {Number} [opts.locktime]
   */
  claim(opts) {
    const contract = this.getContract();
    const utxo = opts?.utxo;
    console.log(opts);

    const transaction = contract.functions.claim(utf8ToBin(opts?.passcode))
      .from(utxo)
      .to(opts?.recipient, BigInt(this.params.payoutSats))
      .withHardcodedFee(this.claimTxFee)
    
    if (Number.isSafeInteger(opts?.locktime)) {
      transaction.withTime(opts?.locktime);
    }

    const remainingSats = utxo?.satoshis - this.claimTxFee - BigInt(this.params.payoutSats);
    if (remainingSats < 0n) {
      return { success: false, error: 'Not enough satoshis' }
    } else if (remainingSats >= 546n) {
      transaction.to(contract.address, remainingSats, utxo?.token)
    }

    return { success: true, transaction }
  }

  /**
   * @param {Object} opts
   * @param {String} opts.wif
   * @param {import("cashscript").Utxo[]} opts.utxos
   * @param {String} opts.recipient
   * @param {Number} [opts.locktime]
   */
  faucetSweep(opts) {
    const recipientAddress = opts?.recipient;
    const recipentTokenAddress = toTokenAddress(recipientAddress);

    const signaureTemplate = new SignatureTemplate(opts?.wif);
    const contract = this.getContract();

    const transaction = contract.functions.ownerUnlock(signaureTemplate, signaureTemplate.getPublicKey()).from(opts?.utxos)
    if (Number.isSafeInteger(opts?.locktime)) {
      transaction.withTime(opts?.locktime);
    }

    // Added outputs, every token utxo will just be passed as is as output
    // The non token utxos will be consolidated
    opts.utxos.map(utxo => {
      if(!utxo.token) return
      transaction.to(recipentTokenAddress, utxo.satoshis, utxo.token);
    })
    const bchUtxos = opts.utxos.filter(utxo => !utxo.token)
    const totalBchUtxos = bchUtxos.reduce((subtotal, utxo) => subtotal + utxo.satoshis, 0n)
    if (totalBchUtxos > 546n) {
      transaction.to(recipientAddress, totalBchUtxos)
    }

    let totalFeeNeeded = BigInt(
      (calculateInputSize(transaction) * transaction.inputs.length) +
      getTxSizeWithoutInputs(transaction.outputs)
    )

    for(let index = transaction.outputs.length - 1; index >= 0; index--) {
      if (totalFeeNeeded <= 0) break;

      const output = transaction.outputs[index];
      const DUST = output.token ? 1000n : 546n;

      if (output.amount < DUST) continue;
      const deductable = output.amount - DUST;
      const toDeduct = deductable < totalFeeNeeded ? deductable : totalFeeNeeded;
      output.amount -= BigInt(toDeduct);
      totalFeeNeeded -= toDeduct;
    }

    if (totalFeeNeeded > 0) {
      return { success: false, error: 'Not enough balance to cover fee' }
    }
    return { success: true, transaction }
  }
}
