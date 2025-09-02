import { binToHex, CashAddressType, decodeCashAddress, encodeCashAddress } from '@bitauth/libauth';

export function addressToPkHash(address='') {
  const decodedAddress = decodeCashAddress(address);
  if (typeof decodedAddress === 'string') throw new Error(decodedAddress)
  
  return binToHex(decodedAddress.payload);
}

export function toTokenAddress(address ='') {
  const decodedAddress = decodeCashAddress(address)
  if (typeof decodedAddress == 'string') throw decodedAddress

  switch(decodedAddress.type) {
    case (CashAddressType.p2pkhWithTokens):
    case (CashAddressType.p2shWithTokens):
      return address
    case (CashAddressType.p2pkh):
      return encodeCashAddress({...decodedAddress, type: CashAddressType.p2pkhWithTokens })?.address
    case (CashAddressType.p2sh):
      return encodeCashAddress({ ...decodedAddress, type: CashAddressType.p2shWithTokens })?.address
  }
}
