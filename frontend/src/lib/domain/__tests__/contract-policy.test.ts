import { describe, expect, it } from 'vitest';
import contract from '../contract.json';
import fielddefs from '../fielddefs.json';

const metadataFields = new Set([...contract.metadataFields.required, ...contract.metadataFields.optional]);
const richFields = new Set(contract.richDataFields.optional);

describe('contract ↔ policy', () => {
  it('mapea assets de fielddefs contra assets del contrato', () => {
    const mappedAssets = new Set([...fielddefs.images, ...fielddefs.videos].map((field) => field.contractAsset));
    expect([...mappedAssets].sort()).toEqual(Object.keys(contract.assets).sort());
  });

  it('mapea campos de fielddefs contra metadata o datos ricos del contrato', () => {
    const fields = [...fielddefs.identity, ...fielddefs.texts, ...fielddefs.rich].map((field) => field.contractField);
    const missing = fields.filter((field) => !metadataFields.has(field) && !richFields.has(field));
    expect(missing).toEqual([]);
  });

  it('define obligatorios exactos de COINDOOR', () => {
    const required = {
      identity: fielddefs.identity.filter((field) => field.required).map((field) => field.key),
      images: fielddefs.images.filter((field) => field.required).map((field) => field.key),
      texts: fielddefs.texts.filter((field) => field.required).map((field) => field.key),
      rich: fielddefs.rich.filter((field) => field.required).map((field) => field.key),
      videos: fielddefs.videos.filter((field) => field.required).map((field) => field.key),
    };

    expect(required).toEqual({
      identity: ['title', 'year', 'developer', 'publisher', 'genre', 'players', 'format'],
      images: ['caratula', 'poster'],
      texts: ['sinopsis'],
      rich: ['accent'],
      videos: [],
    });
  });
});
