function adjustFont() {
    const elements = document.querySelectorAll('.action-button')
    const parent = document.getElementById('command-center')
    elements.forEach(element => {
        if (210 < parent.offsetWidth && parent.offsetWidth < 320) {
            element.style.fontSize = '0.7rem';
        } else if (parent.offsetWidth < 210) {
            element.style.fontSize = '0.65rem';
        } else if (parent.offsetWidth >= 320) {
            element.style.fontSize = '1rem';
        }
    });
}

window.addEventListener('load', function() {
    var iframeContainer = document.getElementById('iframe-container');
    var width = iframeContainer.offsetWidth;
    document.getElementById('embedded-iframe').style.height = width + 'px';
    iframeContainer.style.height = width + 'px';
    document.getElementById('chat-box').style.height = width + 'px';
    document.getElementById('command-center').style.height = (width * 0.5) + 'px';
    adjustFont();
});

window.addEventListener('resize', function() {
    var iframeContainer = document.getElementById('iframe-container');
    var width = iframeContainer.offsetWidth;
    document.getElementById('embedded-iframe').style.height = width + 'px';
    iframeContainer.style.height = width + 'px';
    document.getElementById('chat-box').style.height = width + 'px';
    document.getElementById('command-center').style.height = (width * 0.5) + 'px';
    adjustFont();
});

function areArraysEqual(arr1, arr2) {
    if (arr1.length !== arr2.length) {
        return false;
    }
    for (var i = 0; i < arr1.length; i++) {
        if (arr1[i] !== arr2[i]) {
            return false;
        }
    }
    return true;
}

var gameSaved = false;
var rematch_accepted = false;
var updated = false;
var savedMoves = []

function updateCommandCenter() {
    var existingWebGameMetadata = JSON.parse(localStorage.getItem('web_game_metadata'));
    var currentGameID = sessionStorage.getItem('current_game_id');
    currentGameID = (currentGameID === 'null' ? null : currentGameID);
    if (currentGameID !== null && existingWebGameMetadata.hasOwnProperty(currentGameID)) {
        var webGameMetadata = existingWebGameMetadata[currentGameID];
        var moves = webGameMetadata.alg_moves;
        var movesListContainer = document.getElementById('moves-list');
        var endState = webGameMetadata.end_state;
        const equal_arrays = areArraysEqual(moves, savedMoves)
        if (endState !== '' && !updated) {
            const buttons = document.querySelectorAll(".action-button:not([post-game=true])");
            clearInterval(connectIntervalId);
            buttons.forEach(button => {
                button.remove();
            });
        }
        // Don't keep unnecessarily updating
        if (equal_arrays && updated) {
            return;
        }
        savedMoves = moves
        
        movesListContainer.innerHTML = '';

        for (var i = 0; i < moves.length; i += 2) {
            var move1 = moves[i];
            var move2 = (
                (i + 1 < moves.length) && 
                moves[i + 1] !== '1-0' && 
                moves[i + 1] !== '0-1' && 
                moves[i + 1] !== '½–½'
            ) ? moves[i + 1] : '';

            var moveRow = document.createElement('div');
            moveRow.className = 'move-row ' + (i % 4 === 0 ? '' : 'even-move-row');
            
            var leftHalf = document.createElement('div');
            leftHalf.style.width = '50%';
            leftHalf.textContent = move1;

            var rightHalf = document.createElement('div');
            rightHalf.style.width = '50%';
            rightHalf.textContent = move2;

            if (move1 !== '1-0' && move1 !== '0-1' && move1 !== '½–½') {
                moveRow.appendChild(leftHalf);
                moveRow.appendChild(rightHalf);

                movesListContainer.appendChild(moveRow);
            }

        }

        if (endState === "\u00bd\u2013\u00bd") {
            endState = '½–½';
        }
        var forcedEnd = webGameMetadata.forced_end;
        var endMessagebox = document.getElementById('end-message');
        var finalScorebox = document.getElementById('final-score');
        var endmessage = '';
        if (forcedEnd !== '') {
            if (forcedEnd === 'Draw by mutual agreement' || forcedEnd === 'Stalemate by Threefold Repetition') {
                endmessage += forcedEnd;
                finalScorebox.innerHTML = '½–½';
            } else {
                endmessage += forcedEnd + ' • ';
            }
        }

        if (endState === '1-0') {
            endmessage += `White is Triumphant`;
            endMessagebox.innerHTML = `White is Triumphant`;
            finalScorebox.innerHTML = '1-0';
        } else if (endState === '0-1') {
            endmessage += `Black is Triumphant`;
            finalScorebox.innerHTML = '0-1';
        } else if (endState === '½–½' && forcedEnd !== 'Draw by mutual agreement' && forcedEnd !== 'Stalemate by Threefold Repetition') {
            endmessage += `Stalemate was Reached`;
            finalScorebox.innerHTML = '½–½';
        }

        if (endmessage !== '') {
            endMessagebox.innerHTML = endmessage;
            if (!gameSaved) { // Only execute this once
                gameSaved = true
                var comp_moves = webGameMetadata.comp_moves;
                var FEN_final = webGameMetadata.FEN_final_pos;
                saveHistoricGame(moves.join(','), comp_moves.join('-'), endState, FEN_final, forcedEnd);
            }
            
            document.getElementById("rematchButton").classList.remove("hidden");
            document.getElementById("rematchButton").addEventListener("click", function() {
                rematch_accepted = true
                generateRematchURL();
                document.getElementById("rematchButton").disabled = true;
            }, {once: true});
            updated = true;
        }
    }
}

function saveHistoricGame(alg_moves_str, comp_moves_str, score, FEN_final, forcedEnd) {
    fetch('/save_game/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ 
            game_uuid: game_uuid,
            alg_moves: alg_moves_str,
            outcome: score,
            comp_moves: comp_moves_str,
            FEN: FEN_final,
            termination_reason: forcedEnd
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "error") {
            return;
        }
    })
    .catch(error => {
        console.error('Error uploading game:', error);
    });
}

function resetCommandCenter() {
    savedMoves = [];
    var movesListContainer = document.getElementById('moves-list');
    while (movesListContainer.firstChild) {
        movesListContainer.removeChild(movesListContainer.firstChild);
    }

    var endMessagebox = document.getElementById('end-message');
    var finalScorebox = document.getElementById('final-score');

    movesListContainer.innerHTML = "";
    endMessagebox.innerHTML = ""
    finalScorebox.innerHTML = ""
}

var previousConnected = false
var initCheck = false

window.addEventListener('load', resetCommandCenter);
window.addEventListener('load', updateCommandCenter);

setInterval(updateCommandCenter, 100);

var socket;

function initializeWebSocket() {
    socket = new WebSocket("ws://" + window.location.host + "/ws/chat/" + game_uuid + "/");

    socket.onmessage = function (event) {
        var chat_data = JSON.parse(event.data);
        handleMessage(chat_data["message"]);
    };

    // socket.onclose = function (event) {
    //     // add custom chat highlighted message
    // };

}

function sendMessage(message, type = null) {
    var existingWebGameMetadata = JSON.parse(localStorage.getItem('web_game_metadata'));
    var currentGameID = sessionStorage.getItem('current_game_id');
    currentGameID = (currentGameID === 'null' ? null : currentGameID);
    if (currentGameID !== null && existingWebGameMetadata.hasOwnProperty(currentGameID)) { 
        var webGameMetadata = existingWebGameMetadata[currentGameID];
        var playerColor = webGameMetadata["player_color"];
        var messageObj = {
            message: {
                text: message,
                color: playerColor,
                sender: sender,
                end_state: webGameMetadata["end_state"]
            }
        };
        if (type !== null) {
            if (type.includes("rematch")) {
                messageObj["message"]["log"] = type;
            }
        }
        socket.send(JSON.stringify(messageObj));
    } else {
        console.warn("Cannot send message");
    }
}

function handleMessage(data) {
    if (data.hasOwnProperty('log')) {
        if (data["log"] === "disconnect") {
            // Add highlighted message to chat
        }
        return;
    }
    $(".chat-messages").append('<p>' + data["sender"] + ": " + data["text"] + '</p>');
}

function generateRematchURL() {
    fetch('/create_new_game/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ 
            computer_game: true
        }),
    })
    .then(response => {
        if (response.status === 200) {
            return response.json();
        } else {
            console.error('Error creating game:', response.statusText);
            return Promise.reject('Error creating game');
        }
    })
    .then(data => {
        if (data.redirect) {
            window.location.href = data.url;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function updateConnectedStatus(status) {
    fetch('/update_connected/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ 
            game_uuid: game_uuid, 
            web_connect: status
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "error" && data.message === "Lobby row DNE") {
            return;
        }
        // Handle the response as needed
        // Put in a "waiting message" if it hasn't been played yet
        // Put a disconnect status if in play
        // Later have reconnects connect to the websocket and 
        // any disconnects disconnect from the websocket can have 
        // a variable tracking socket connection status
    })
    .catch(error => {
        console.error('Error updating connection status:', error);
    });
}

function checkNewConnect() {
    var currentConnected = sessionStorage.getItem('connected');
    currentConnected = (currentConnected === 'true' ? true : false);
    if (currentConnected === true && previousConnected === false) {
        updateConnectedStatus(true)
    }
    
    var initialized = sessionStorage.getItem('initialized');
    initialized = (initialized === 'true' ? true : false);
    if (initialized === true && initCheck === false) {
        const idStrings = ["undoOfferButton", "resignButton", "cycleThemeButton", "flipButton"];
        idStrings.forEach(idString => {
            document.getElementById(idString).classList.remove("hidden")
        })
        initializeWebSocket();
        initCheck = initialized
    }

    previousConnected = currentConnected;
}

var connectIntervalId = setInterval(checkNewConnect, 1000);

window.onbeforeunload = function () {
    if (!rematch_accepted) {
        return true;
    }
};

// to defaults
window.addEventListener('beforeunload', function () {
    sessionStorage.setItem('connected', 'false');
    sessionStorage.setItem('current_game_id', game_uuid);
    sessionStorage.setItem('initialized', 'null');
});

var eventExecutionStatus = {};

function handleWebtoGameAction(buttonId, localStorageObjectName, Options = null) {
    var existingWebGameMetadata = JSON.parse(localStorage.getItem('web_game_metadata'));
    var currentGameID = sessionStorage.getItem('current_game_id');
    currentGameID = (currentGameID === 'null' ? null : currentGameID);
    if (currentGameID !== null && existingWebGameMetadata.hasOwnProperty(currentGameID)) { 
        var webGameMetadata = existingWebGameMetadata[currentGameID];
        webGameMetadata[localStorageObjectName].execute = true
        existingWebGameMetadata[currentGameID] = webGameMetadata
        localStorage.setItem('web_game_metadata', JSON.stringify(existingWebGameMetadata));

        if (!eventExecutionStatus[localStorageObjectName]) {
            eventExecutionStatus[localStorageObjectName] = { isExecuting: false, timeoutId: null };
        }

        handleActionStatus(buttonId, currentGameID, localStorageObjectName, Options);

    } else {
        console.warn("Failed to execute action")
    }
}

var actionEventList = [
    {mainButtonName: "undoOfferButton", eventNames: ["undo_move"]},
    {mainButtonName: "resignButton", eventNames: ["resign"]}
]

var inputList = [
    { buttonId: "undoOfferButton", localStorageObjectName: "undo_move", Options: "followups"},
    { buttonId: "resignButton", localStorageObjectName: "resign", Options: "followups"},
    { buttonId: "cycleThemeButton", localStorageObjectName: "cycle_theme"},
    { buttonId: "flipButton", localStorageObjectName: "flip_board"},
];

function handleActionStatus(buttonId, currentGameID, localStorageObjectName) {
    var existingWebGameMetadata = JSON.parse(localStorage.getItem('web_game_metadata'));
    var webGameMetadata = existingWebGameMetadata[currentGameID];
    var actionCommandStatus = webGameMetadata[localStorageObjectName];
    
    // console.log(localStorageObjectName, actionCommandStatus) // Good dev log, very good boy
    var initialDefaults = (!actionCommandStatus.execute && !actionCommandStatus.update_executed);
    if (!actionCommandStatus.update_executed && !initialDefaults) {
        eventExecutionStatus[localStorageObjectName].timeoutId = setTimeout(function () {
            // This can be too fast and execute again right before reset is set to false, 
            // hence the default condition check
            handleActionStatus(buttonId, currentGameID, localStorageObjectName);
        }, 10);
    } else {
        webGameMetadata[localStorageObjectName].execute = false
        webGameMetadata[localStorageObjectName].update_executed = false

        existingWebGameMetadata[currentGameID] = webGameMetadata
        localStorage.setItem('web_game_metadata', JSON.stringify(existingWebGameMetadata));
        
        document.getElementById(buttonId).disabled = false;
    }
}

function optionStringsHelper(mainbuttonId) {
    var approveString = "Confirm";
    var abandonString = "Cancel";
    var replaceString = "Button";
    const buttonApproveId = mainbuttonId.replace(replaceString, approveString + "Button");
    const buttonAbandonId = mainbuttonId.replace(replaceString, abandonString + "Button");
    return {ApproveId: buttonApproveId, AbandonId: buttonAbandonId, AbandonStr: abandonString}
}

function hideOptions(buttonId, buttonApproveId, buttonAbandonId) {
    document.getElementById(buttonId).classList.remove("hidden");
    document.getElementById(buttonApproveId).classList.add("hidden");
    document.getElementById(buttonAbandonId).classList.add("hidden");
}

function showOptions(buttonId, buttonApproveId, buttonAbandonId) {
    document.getElementById(buttonId).classList.add("hidden");
    document.getElementById(buttonApproveId).classList.remove("hidden");
    document.getElementById(buttonAbandonId).classList.remove("hidden");
}

inputList.forEach(function(input) {
    const optionsValue = (input.hasOwnProperty("Options") ? input.Options: null);
    document.getElementById(input.buttonId).addEventListener("click", function() {
        handleButton(input.buttonId, input.localStorageObjectName, optionsValue);
    });
});

function eventIsExecuting(obj, eventNames) {
    for (var event of eventNames) {
        if (obj.hasOwnProperty(event) && obj[event]["execute"] === true) {
            return true;
        }
    }
    return false;
}

function handleButton(buttonId, localStorageObjectName, Options = null) {
    document.getElementById(buttonId).disabled = true;
    if (Options !== null) {
        result = optionStringsHelper(buttonId, Options)
        const buttonApproveId = result.ApproveId
        const buttonAbandonId = result.AbandonId
        document.getElementById(buttonId).classList.add("hidden");
        document.getElementById(buttonApproveId).classList.remove("hidden");
        document.getElementById(buttonAbandonId).classList.remove("hidden");
        var otherFollowups = document.querySelectorAll('[followup="true"]');

        otherFollowups.forEach(function(element) {
            if (element.id !== buttonApproveId && element.id !== buttonAbandonId) {
                element.classList.add("hidden");
            }
        });
        var actionbuttons = document.querySelectorAll('[actions="true"]');
        var existingWebGameMetadata = JSON.parse(localStorage.getItem('web_game_metadata'));
        var currentGameID = sessionStorage.getItem('current_game_id');
        var webGameMetadata = existingWebGameMetadata[currentGameID];
        
        // On followup display only, main buttons are disabled. We need to re-enable them
        // This does not apply to executing actions
        actionbuttons.forEach(function(element) {
            if (element.id !== buttonId) {
                element.classList.remove("hidden");
                var actionEvents = actionEventList.find(event => event.mainButtonName === element.id)
                var notExecuting = !eventIsExecuting(webGameMetadata, actionEvents.eventNames)
                if (notExecuting) {
                    element.disabled = false;
                }
            }
        });
        document.getElementById(buttonApproveId).addEventListener("click", function() { 
            hideOptions(buttonId, buttonApproveId, buttonAbandonId)
            handleWebtoGameAction(buttonId, localStorageObjectName, Options);
        }, { once: true });
        document.getElementById(buttonAbandonId).addEventListener("click", function() {
            hideOptions(buttonId, buttonApproveId, buttonAbandonId)
            document.getElementById(buttonId).disabled = false;
        }, { once: true });
    } else {
        handleWebtoGameAction(buttonId, localStorageObjectName)
    };
}

// // Logging Debug python console messages; Only for development hence keep it commented. Maybe add a global dev flag too
// function pythonDebugLogger() {
//     var logs = webGameMetadata.console_messages
//     for (var i = 0; i < logs.length; i++) {
//         console.log(logs[i])
//     }
// }

// window.addEventListener('load', pythonDebugLogger);

// // Set up an interval to log debug print statements
// setInterval(pythonDebugLogger, 1000);