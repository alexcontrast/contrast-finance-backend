const fs = require('fs');
const {context} = require('./test_manager_editor.cjs');
const cases = JSON.parse(fs.readFileSync(0,'utf8'));
const answers=cases.map(input=>{
  const c=context();
  c.state.bootstrap.economics=input.economics;
  return c.calculateDraftSummaryPreview(input.items,input.event,{});
});
process.stdout.write(JSON.stringify(answers));
