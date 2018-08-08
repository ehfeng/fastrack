const {NodeVM} = require('vm2');
const zlib = require('zlib');
const Raven = require('raven');
const https = require('https');

var nodeVm = new NodeVM({
	console: 'redirect',
    require: {
        external: true
  }
});

global.event_id;
global.logs = [];
global.code = '';

exports.hello = (req, res) => {
  res.set('Access-Control-Allow-Origin', '*')
  res.set("Access-Control-Allow-Methods", "POST");
  res.set("Access-Control-Allow-Headers", "Content-Type");
  res.set("Content-Type", "application/json");
  if (req.method == "OPTIONS") {
    console.log('options was hit');
    res.status(204).send('').end();
  }

  var raven_callback = () => {
    res.send(JSON.stringify({event_id: global.event_id, logs: global.logs}));
  }

  var sendEvent = (dsn, kwargs) => {
    frame = kwargs.exception[0].stacktrace.frames[kwargs.exception[0].stacktrace.frames.length - 1]
    console.log('body: ', global.code);
    let code_array = global.code.split('\n')
    frame.context_line = code_array[frame.lineno - 1]
    frame.post_context = code_array.slice(frame.lineno, code_array.length)
    frame.pre_context = code_array.slice(0, frame.lineno - 1)
    Raven.config(`https://${dsn.public_key}@${dsn.host}/${dsn.project_id}`).install();
    Raven.send(kwargs, raven_callback);
  }

  nodeVm.on('console.log', (msg) => {
    global.logs.push(msg)
  })

  process.on('SENTRY_EVENT_PROCESS', (msg) => {
    console.log('SENTRY_EVENT_PROCESS was hit');
    kwargs = JSON.parse(msg.kwargs)
    global.event_id = kwargs.event_id
    sendEvent(msg.dsn, kwargs);
    console.log('almost everything was hit')
    
  })
  global.code = req.body.code;
  nodeVm.run(req.body.code, 'main.js');
}