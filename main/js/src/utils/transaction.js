import { hexToBin, isHex } from '@bitauth/libauth';
import { SignatureTemplate, Transaction } from "cashscript";
import { placeholder } from "@cashscript/utils"

import { createInputScript, getInputSize } from "cashscript/dist/utils.js";

/**
 * Taken directly from Transaction class' fee calculation
 * Returns the bytesize of contract's transaction input
 * @param {Transaction} transaction
 */
export function calculateInputSize(transaction) {
  const placeholderArgs = transaction.encodedFunctionArgs.map((arg) => (arg instanceof SignatureTemplate ? placeholder(71) : arg));

  // Create a placeholder preimage of the correct size
  // const placeholderPreimage = transaction.abiFunction.covenant
  //     ? placeholder(getPreimageSize(scriptToBytecode(transaction.contract.redeemScript)))
  //     : undefined;

  // Create a placeholder input script for size calculation using the placeholder
  // arguments and correctly sized placeholder preimage
  const placeholderScript = createInputScript(transaction.contract.redeemScript, placeholderArgs, transaction.selector);
  // Add one extra byte per input to over-estimate tx-in count
  const contractInputSize = getInputSize(placeholderScript);
  return contractInputSize
}


/**
 * @param {Object} utxo
 * @param {String} utxo.txid
 * @param {Number} utxo.vout
 * @param {Number | String} utxo.satoshis
 * @param {Object} [utxo.token]
 * @param {Number | String} utxo.token.amount
 * @param {String} utxo.token.category
 * @param {Object} [utxo.token.nft]
 * @param {'none' | 'mutable' | 'minting'} utxo.token.nft.capability
 * @param {String} utxo.token.nft.commitment
 * @param {String} [utxo.wif]
 * @returns {import('cashscript').Utxo | import('cashscript').UtxoP2PKH}
 */
export function parseUtxo(utxo) {
  const result = {
    txid: utxo?.txid,
    vout: utxo?.vout,
    satoshis: BigInt(utxo?.satoshis),
    token: !utxo?.token ? undefined : {
      category: utxo?.token?.category,
      amount: BigInt(utxo?.token?.amount),
      nft: !utxo?.token?.nft ? undefined : {
        capability: utxo?.token?.nft?.capability,
        commitment: utxo?.token?.nft?.commitment,
      }
    },
  }
  if (utxo?.wif) result.template = new SignatureTemplate(utxo?.wif)

  return result
}

/**
 * @param {Object} output 
 * @param {String} output.to
 * @param {Number} output.amount
 * @param {Object} [output.token]
 * @param {Number | String} output.token.amount
 * @param {String} output.token.category
 * @param {Object} [output.token.nft]
 * @param {'none' | 'mutable' | 'minting'} output.token.nft.capability
 * @param {String} output.token.nft.commitment
 * @returns {import('cashscript').Output}
 */
export function parseCashscriptOutput(output) {
  return {
    to: isHex(output?.to) ? hexToBin(output?.to) : output?.to,
    amount: BigInt(output?.amount),
    token: !output?.token ? undefined : {
      category: output?.token?.category,
      amount: BigInt(output?.token?.amount),
      nft: !output?.token?.nft ? undefined : {
        capability: output?.token?.nft?.capability,
        commitment: output?.token?.nft?.commitment,
      }
    },
  }
}
