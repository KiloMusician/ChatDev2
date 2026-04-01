// Example jscodeshift transformer
// Usage: npx jscodeshift -t ops/codemods/ts/rename-symbol.template.ts src
const transformer = (file, api) => {
  const j = api.jscodeshift;
  
  return j(file.source)
    .find(j.Identifier, { name: 'oldName' })
    .replaceWith(j.identifier('newName'))
    .toSource();
};

module.exports = transformer;