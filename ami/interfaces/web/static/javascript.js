const updateClock = () => {
    const clock = document.getElementById("clock");

    const now = new Date();

    let hours = now.getHours();
    let minutes = now.getMinutes();
    let seconds = now.getSeconds();

    hours   > 12 ? hours - 12 : hours;
    const period = hours >= 12 ? ' PM' : ' AM';

    hours   < 10 ? '0' + hours   : '' + hours;
    minutes < 10 ? '0' + minutes : '' + minutes;
    seconds < 10 ? '0' + seconds : '' + seconds;

    const formattedTime = `${hours} : ${minutes} . ${seconds}${period}`;
       
    clock.innerHTML = formattedTime;
};

setInterval(updateClock,1000);
updateClock();

function openPopup() {
    var popup = document.createElement("div");
    popup.setAttribute("class", "popup");
    popup.setAttribute("id", "popup");

    countdownBar = document.createElement("div")
    countdownBar.setAttribute("id", "countdown-bar")

    popup.appendChild(countdownBar)

    document.body.appendChild(popup);
    //shrinkBar(10);
}

function removePopup() {
    var popup = document.getElementById("popup");

    if (popup != null) {
        document.body.removeChild(popup);
    }
}

function shrinkBar(duration) {
   var div = document.getElementById('countdown-bar');
   
   // Set custom property for animation duration
   div.style.setProperty('--animation-time', duration + 's');

   div.classList.add('shrink');

   setTimeout(removePopup, duration * 1000);
}

function getChat(html) {
    var chat = document.createElement("div");
    chat.setAttribute("class", "chat-element");
    chat.innerHTML = html

    return chat;
}
function appendChat(text) {
    var popup = document.getElementById("popup");
    if (popup != null) {
        var chat = getChat(text);
        popup.appendChild(chat);
    }
}
function loadCalendar() {

    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/calendar');

    xhr.onload = function() {
        if (xhr.status === 200) {
            document.getElementById("calendar").innerHTML = xhr.responseText;
        } else {
            document.getElementById("calendar").innerHTML =  xhr.status;
        }
    };
  
    xhr.onerror = function() {
        console.log('Request failed');
    };

    xhr.send();
}

function getMarkdown(side) {
    return new Promise(function(resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/markdown/' + side);
        xhr.onload = function() {
            if (xhr.status === 200) {
                resolve(xhr.responseText);
            } else {
                reject(xhr.status);
            }
        };
        xhr.onerror = function() {
            reject('Request failed');
        };
        xhr.send();
    });
}

function getMarkdownSection(path) {
    return new Promise(function(resolve, reject) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/markdown/' + path);
        xhr.onload = function() {
            if (xhr.status === 200) {
                resolve(xhr.responseText);
            } else {
                reject(xhr.status);
            }
        };
        xhr.onerror = function() {
            reject('Request failed');
        };
        xhr.send();
    });
}

async function loadMarkdowns() {
    try {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/api/config-markdowns');
        xhr.onload = async function() {
            if (xhr.status === 200) {
                var markdownPaths = JSON.parse(xhr.responseText);
                var section = document.getElementById("bottom");
                markdown_html = ""
                for (var path of markdownPaths) {
                    try {
                        var markdown = await getMarkdownSection(path);
                        markdown_html += markdown;
                    } catch (error) {
                        console.log('Failed to load markdown:', path, error);
                    }
                    section.innerHTML = markdown_html;
                }
            } else {
                console.log('Request failed. Status:', xhr.status);
            }
        };
        xhr.onerror = function() {
            console.log('/api/config-markdowns failed.');
        };
        xhr.send();
    } catch (error) {
        console.log('Error loading markdowns:', error);
    }
}

function reload() {
    loadCalendar();
    loadMarkdowns();
}

document.addEventListener("DOMContentLoaded", function() {  reload();  });