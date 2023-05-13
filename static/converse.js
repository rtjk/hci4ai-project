/*
  Basic Voice User Interface.

  It uses the Web Speech API (experimental) for speech-to-text and text-to-speech operations.
  Tested in Chrome 57+, Firefox 70+, and Safari 10.1+.
  Please, notice that speech-to-text capability does not work in Safari and Firefox.
*/
let $speechInput,
  $recBtn,
  recognition,
  mute = false,
  messageRecording = ["Recording..."],
  messageCouldntHear = ["I couldn't hear you, could you repeat?"],
  messageInternalError = ["Oh no, there has been an internal server error"],
  messageSorry = ["I'm sorry, I don't have the answer to that yet."],
  $muteBtn;



$(document).ready(function() {
  $speechInput = $("#userquery");
  $recBtn = $("#rec");
  $muteBtn = $("#mute");

  // get the text inserted by the user and process it
  $speechInput.keypress((event) => {
    if (event.which === 13) { // 13 is carriage return (new line)
      event.preventDefault();
      if($speechInput.val()!=="") {
        // add the new message in the chat area
        createBubbleChat($speechInput.val(), "self");
        // send the text to the server
        send();
        // clear the input
        $speechInput.val("");
      }
    }
  });
  $recBtn.on("click", function(event) {
    // start or stop speech recognition
    switchRecognition();
  });
  $muteBtn.on("click", function(event) {
    switchMute();
  });
});

/* Functions related to the Web Speech API (speech-to-text) */
function startRecognition() {
  SpeechRecognition = webkitSpeechRecognition || SpeechRecognition;
  recognition = new SpeechRecognition();
  // the recording stops when the user stops talking
  recognition.continuous = false;
  // the only results returned by the recognizer are final
  recognition.interimResults = false;

  // what happens when the recording starts...
  recognition.onstart = (event) => {
    respond(messageRecording);
    updateRec();
  };

  //... when the recording service ends...
  recognition.onend = (event)  => {
    respond(messageCouldntHear);
    stopRecognition();
  };

  // ... and when results (transcriptions) are available
  recognition.onresult = (event)  => {
    recognition.onend = null;

    let text = "";
    // The SpeechRecognitionEvent results property returns a SpeechRecognitionResultList object,
    // which contains SpeechRecognitionResult objects. Each of them contains SpeechRecognitionAlternative objects,
    // with individual results.
    // The resultIndex property returns the lowest index value that has actually changed
    for(let i = event.resultIndex; i <event.results.length; i++) {
      text += event.results[i][0].transcript;
    }
    setInput(text);
    stopRecognition();
  };

  recognition.lang = "en-US";
  recognition.start();
}

function stopRecognition() {
  if(recognition) {
    recognition.stop();
    recognition = null;
  }
  updateRec();
}

function switchRecognition() {
  if (recognition) {
    stopRecognition();
  } else {
    startRecognition();
  }
}

function switchMute() {
  if (mute == true) {
      mute = false
      $muteBtn.html('<i class="fa fa-volume-up fa-lg" aria-hidden="true"></i>')
    } else {
    mute = true
    window.speechSynthesis.cancel()
    $muteBtn.html('<i class="fa fa-volume-off fa-lg" aria-hidden="true"></i>')
  }
}

/* Change the mic icon from in-use to not */
function updateRec() {
  start = '<i class="fa fa-microphone fa-lg" aria-hidden="true"></i>';
  end = '<i class="fa fa-microphone-slash fa-lg" aria-hidden="true"></i>';
  $recBtn.html(recognition ? end : start);
}


/* Set the recognized text as textual input for further processing */
function setInput(text) {
  $speechInput.val(text);
  createBubbleChat($speechInput.val(), "self");
  send();
  $speechInput.val("");
}

/* Send the input message for further processing */
// it uses the Web Speech API for performing text-to-speech
function send() {
  let text = $speechInput.val();
  $.ajax({
    type: "POST",
    url: "/dialog_ask",
    contentType: "application/json",
    data: '{"text":"' + text + '"}',

    success: function(data) {
      respond(data);
    },
    error: function() {
      respond(messageInternalError);
    },
    dataType: "json"
  });
}

/* Handle the response coming from the server */
function respond(val) {
  if (val === "") {
    val = messageSorry;
  }

  if(val !== messageRecording) {
    for (const valKey in val) {
      if (val[valKey].substring(0,2) != "b'") {
        let msg = new SpeechSynthesisUtterance();
        msg.text = val[valKey];
        msg.lang = "en-US";
        if (mute==false)
          window.speechSynthesis.speak(msg);
      }

      // add the new message in the chat area
      createBubbleChat(val[valKey], "other");
    }

  }
}

//--- Utility functions ---//

/* Create a new "chat bubble" in the chat area */
function createBubbleChat(val, type){
  console.log(val.replace("b'","").replace("'",""))
  if (val.substring(0,2) == "b'")
    $(".chat").append('<li class="'+type+'"><div class="msg"><img style="border-radius: 10px" src="data:image/png;base64,' + val.replace("b'","").replace("'","") + '" alt="Pneumonia img"/></div></li>');
  else
    $(".chat").append('<li class="'+type+'"><div class="msg"><p>'+val+'</p></div></li>');
  //setTimeout(function(){window.scrollTo(0,document.body.scrollHeight);},500)
  window.scrollTo(0,document.body.scrollHeight);
}
