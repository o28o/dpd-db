const c = console.log

//// elements

const docBody = document.body
const titleClear = document.getElementById("title-clear")
const mainPane = document.getElementById("main-pane");
const dpdPane = document.getElementById("dpd-pane");
const summaryResults = document.getElementById("summary-results");
const dpdResults = document.getElementById("dpd-results");
const historyPane = document.getElementById("history-pane");
const historyListPane = document.getElementById("history-list-pane");
const subTitle = document.getElementById("subtitle")
const searchBox = document.getElementById("search-box")
const entryBoxClass = document.getElementsByClassName("search-box")
const searchForm = document.getElementById("search-form");
const searchButton = document.getElementById("search-button");
const footerText = document.getElementById("footer");

const themeToggle = document.getElementById("theme-toggle");
const sansSerifToggle = document.getElementById("sans-serif-toggle");
const niggahitaToggle = document.getElementById("niggahita-toggle");
const grammarToggle = document.getElementById("grammar-toggle");
const exampleToggle = document.getElementById("example-toggle");
const oneButtonToggle = document.getElementById("one-button-toggle");
// const sbsexampleToggle = document.getElementById("sbs-example-toggle");
const summaryToggle = document.getElementById("summary-toggle");
const sandhiToggle = document.getElementById("sandhi-toggle");
var fontSize
const fontSizeUp = document.getElementById("font-size-up");
const fontSizeDown = document.getElementById("font-size-down");
var fontSizeDisplay = document.getElementById("font-size-display");

let dpdResultsContent = "";
let language;

//// uri utils

function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split('&');

    for (var i = 0; i < vars.length; i++) {
      var pair = vars[i].split('=');

      if (pair[0] === variable) {
        return decodeURIComponent(pair[1].replace(/\+/g, '%20'));
      }
    }
}

//// load state

function loadToggleState(id) {
    var savedState = localStorage.getItem(id);
    if (savedState !== null) {
        document.getElementById(id).checked = JSON.parse(savedState);
    }
}

//// Page load
document.addEventListener("DOMContentLoaded", function() {
    const htmlElement = document.documentElement;
    language = htmlElement.lang || 'en';
    let startMessage;

    if (language === 'en') {
        startMessage = `
      <p class="message">Search in Pāḷi or English using <b>Autocomplete</b>, <b>Unicode</b> or <b>Velthuis</b>.</p>
<p class="message"><b>Double-click</b> any word to search.</p>
<p class="message">Adjust <b>Settings</b> as needed.</p>
<p class="message"><b>Refresh</b> if issues occur.</p>
<p class="message">
    More info about: <a href="https://docs.dpdict.net/dpdict.html" target="_blank">Site</a> or 
    <a href="https://docs.dpdict.net/titlepage.html" target="_blank">DPD in general</a>.
</p>
<p class="message">Try: <b>Double-click</b> words below:</p>
<p class="message">atthi kāmarāgapariyuṭṭhitena peace kar gacchatīti Root✓</p>
`;
    } else if (language === 'ru') {
        startMessage = `
        <p class="message">Ищите на пали или русском с <b>Автоподсказками</b>, <b>Unicode</b> или <b>Velthuis</b>.</p>
<p class="message"><b>Двойной клик</b> по слову для поиска.</p>
<p class="message"><b>Настройки</b> — доп. функции.</p>
<p class="message"><b>Обновите</b> страницу при проблемах.</p>
<p class="message">
    Подробнее о: <a href="https://digitalpalidictionary.github.io/rus/dpdict.html" target="_blank">Сайте</a> или
    <a href="https://digitalpalidictionary.github.io/rus/" target="_blank">DPD в целом</a>.
</p>
<p class="message">Попробуйте: <b>двойной клик</b> по словам ниже:</p>
<p class="message">atthi kāmarāgapariyuṭṭhitena peace kar gacchatīti Root✓</p>
        `;
    }

    if (dpdResults.innerHTML.trim() === "") {
        dpdResults.innerHTML = startMessage;
    }

    applySavedTheme();
    populateHistoryBody();
    loadToggleState("theme-toggle");
    loadToggleState("sans-serif-toggle");
    loadToggleState("niggahita-toggle");
    loadToggleState("grammar-toggle");
    loadToggleState("example-toggle");
    loadToggleState("one-button-toggle");
    // loadToggleState("sbs-example-toggle");
    loadToggleState("summary-toggle");
    loadToggleState("sandhi-toggle");
    loadFontSize();
    toggleClearHistoryButton();
    swopSansSerif();
    applyUrlQuery();

    // Language switcher dropdown control
    const languageIcon = document.querySelector(".language-icon");
    const dropdown = document.querySelector(".dropdown");

    // Ensure both elements exist before adding event listeners
    if (languageIcon && dropdown) {
        // Show or hide dropdown on icon click
        languageIcon.addEventListener("click", function () {
            dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
        });

        // Hide dropdown if clicked outside
        document.addEventListener("click", function (e) {
            if (!languageIcon.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = "none";
            }
        });
    } else {
        console.error("Error: .language-icon or .dropdown element not found in the DOM.");
    }
});

//// listeners

//// back button

window.onpopstate = function(e) {
    if (e.state !=null) {
        searchBox.value = e.state.q;
        handleFormSubmit().then();
    }
};

//// trigger title clear - go home

titleClear.addEventListener("dblclick", function() {
	dpdPane.innerHTML = ""; 
});

//// double click to search 

dpdPane.addEventListener("dblclick", processSelection);
historyPane.addEventListener("dblclick", processSelection);

function processSelection() {
    var selection = window.getSelection().toString();
    searchBox.value = selection;
    if (selection.trim() !== "") {
        handleFormSubmit();
    }
};

//// font size ////

function loadFontSize() {
    fontSize = localStorage.getItem("fontSize");
    if (fontSize === null) {
        bodyStyle = window.getComputedStyle(document.body);
        fontSize = parseInt(bodyStyle.getPropertyValue('font-size'), 10);
    } else {
        setFontSize()
    }
}

function saveFontSize() {
    localStorage.setItem("fontSize", fontSize);
}

function setFontSize() {
    document.body.style.fontSize = fontSize + "px"
    fontSizeDisplay.innerHTML =`${fontSize}px`
}

fontSizeUp.addEventListener("click", increaseFontSize)
fontSizeDown.addEventListener("click", decreaseFontSize)

function increaseFontSize() {
    fontSize = parseInt(fontSize, 10) + 1
    setFontSize()
    saveFontSize()
}

function decreaseFontSize() {
    fontSize = parseInt(fontSize, 10) - 1
    setFontSize()
    saveFontSize()
}


// Модифицированная функция changeLanguage
function changeLanguage(lang) {
  // Получаем текущий URL и разбиваем его на части
  const url = new URL(window.location.href);
  let path = url.pathname; // Путь (например, "/ru")
  const searchParams = url.search; // Параметры запроса (например, "?q=dukkha")
  const hash = url.hash; // Хэш (например, "#section")

  // Удаляем все существующие вхождения '/ru' из пути
  path = path.replace(/^\/ru/, '');

  // Если выбран язык 'ru', добавляем '/ru' в начало пути
  if (lang === 'ru') {
    path = '/ru' + path;
  }

  // Обновляем путь в URL
  url.pathname = path;

  // Принудительно обновляем страницу с новым URL
  window.location.href = url.toString();
}
//// enter or click button to search 

searchForm.addEventListener("submit", handleFormSubmit);
searchButton.addEventListener("submit", handleFormSubmit);

//// submit search

async function handleFormSubmit(event) {
    if (event) {
        event.preventDefault();
    }
    const searchQuery = searchBox.value;
    if (searchQuery.trim() !== "") {
        try {
            addToHistory(searchQuery);
            // Adjust the search URL based on the current language
            let searchUrl = '/search_json';
            if (language === 'ru') {
                searchUrl = '/ru/search_json';
            }
            const response = await fetch(`${searchUrl}?q=${encodeURIComponent(searchQuery)}`);
            const data = await response.json(); 

            //// add the summary_html
            if (data.summary_html.trim() != "") {
                if (language === 'en') {
                    summaryResults.innerHTML = "<h3>Summary</h3>";
                } else {
                    summaryResults.innerHTML = "<h3>Сводка</h3>";
                }
                summaryResults.innerHTML += data.summary_html; 
                summaryResults.innerHTML += "<hr>";
            } else {
                summaryResults.innerHTML = "";
            }
            showHideSummary();

            //// add dpd_html
            const dpdDiv = document.createElement("div");
            dpdDiv.innerHTML += data.dpd_html;
            
            //// niggahita toggle
            if (niggahitaToggle.checked) {
                niggahitaUp(dpdDiv);
            }
    
            //// grammar button toggle
            if (grammarToggle.checked) {
                const grammarButtons = dpdDiv.querySelectorAll('[name="grammar-button"]');
                const grammarDivs = dpdDiv.querySelectorAll('[name="grammar-div"]');
                grammarButtons.forEach(button => {
                    button.classList.add("active");
                });
                grammarDivs.forEach(div => {
                    div.classList.remove("hidden");
                });
            };
    
            //// example button toggle
            if (exampleToggle.checked) {
                const exampleButtons = dpdDiv.querySelectorAll('[name="example-button"]');
                const exampleDivs = dpdDiv.querySelectorAll('[name="example-div"]');
                exampleButtons.forEach(button => {
                    button.classList.add("active");
                });
                exampleDivs.forEach(div => {
                    div.classList.remove("hidden");
                });
            };

            // //// sbs example button toggle
            // if (sbsexampleToggle.checked) {
            //     const sbsexampleButtons = dpdDiv.querySelectorAll('[name="sbs-example-button"]');
            //     const sbsexampleDivs = dpdDiv.querySelectorAll('[name="sbs-example-div"]');
            //     sbsexampleButtons.forEach(button => {
            //         button.classList.add("active");
            //     });
            //     sbsexampleDivs.forEach(div => {
            //         div.classList.remove("hidden");
            //     });
            // };

            dpdResults.innerHTML = dpdDiv.innerHTML;
            dpdResultsContent = dpdDiv.innerHTML;

            //// sandhi button toggle
            showHideSandhi();
            
            populateHistoryBody();
            dpdPane.focus();
            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });
            dpdPane.scrollTo({
                top: 0,
                behavior: "smooth"
            });

            dpdPane.scrollTo({
                top: 0,
                behavior: "smooth"
            });

            // Update the URL with the search query
            let url = `/?q=${encodeURIComponent(searchQuery)}`;
            history.pushState({ q: searchQuery }, "", url);
            
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    } else {
        // Clear the URL if the search query is empty
        history.pushState({ q: '' }, "", "/");
    }
}

//// url query param

function applyUrlQuery() {
    const query = getQueryVariable('q');
    if(!query) return;
    searchBox.value = query;
    window.history.replaceState({'q': query}, '', '?q='+encodeURIComponent(query));
    handleFormSubmit().then();
}

//// populate history

function addToHistory(word) {
    let historyList = JSON.parse(localStorage.getItem("history-list")) || [];
    const index = historyList.indexOf(word);
    if (index !== -1) {
        historyList.splice(index, 1);
    }
    historyList.unshift(word);
    if (historyList.length > 50) {
        historyList.pop();
    }
    localStorage.setItem("history-list", JSON.stringify(historyList));
    if (getQueryVariable('q') !== word) {
        window.history.pushState({'q': word}, '', '?q='+encodeURIComponent(word));
    }
    toggleClearHistoryButton()
}

function populateHistoryBody() {
    let historyList = JSON.parse(localStorage.getItem("history-list")) || [];
    let listElement = document.createElement("ul");
    listElement.id = "history-list";

    historyList.forEach(item => {
        let listItem = document.createElement("li");
        listItem.textContent = item;
        listElement.appendChild(listItem);
    });

    historyListPane.innerHTML = ""; 
    historyListPane.appendChild(listElement);
}

document.getElementById("clear-history-button").addEventListener("click", function() {
    localStorage.removeItem("history-list");
    document.getElementById("history-list").innerHTML = "";
    toggleClearHistoryButton()
});

function toggleClearHistoryButton() {
    let historyList = JSON.parse(localStorage.getItem("history-list")) || [];
    let clearHistoryButton = document.getElementById("clear-history-button");

    if (historyList.length === 0) {
        clearHistoryButton.style.display = "none";
    } else {
        clearHistoryButton.style.display = "inline-block";
    }
}


//// save settings on toggle

themeToggle.addEventListener("change", saveToggleState);
sansSerifToggle.addEventListener("change", saveToggleState);
niggahitaToggle.addEventListener("change", saveToggleState);
grammarToggle.addEventListener("change", saveToggleState);
exampleToggle.addEventListener("change", saveToggleState);
oneButtonToggle.addEventListener("change", saveToggleState);
// sbsexampleToggle.addEventListener("change", saveToggleState);
summaryToggle.addEventListener("change", saveToggleState);
sandhiToggle.addEventListener("change", saveToggleState);

function saveToggleState(event) {
    localStorage.setItem(event.target.id, event.target.checked);
}

//// theme

function toggleTheme(event) {
    document.body.classList.toggle("dark-mode", event.target.checked);
    localStorage.setItem("theme", event.target.checked ? "dark" : "light");
}

//// Event listener for theme toggle
themeToggle.addEventListener("change", toggleTheme);

//// Function to apply the saved theme state
function applySavedTheme() {
    var savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
        document.body.classList.remove("dark-mode", "light-mode"); // Remove both classes
        document.body.classList.add(savedTheme + "-mode"); // Add the saved theme class
        themeToggle.checked = savedTheme === "dark"; // Sync toggle state
    }
}

//// toggle sans / serif

sansSerifToggle.addEventListener("change", function() {
    swopSansSerif()
});

function swopSansSerif() {
    const serifFonts = '"Noto Serif", "Dejavu Serif", "Garamond", "Georgia", "serif"';
    const sansFonts = '"Roboto", "Dejavu Sans", "Noto Sans", "Helvetica", "Verdana", "sans-serif"';
    if (sansSerifToggle.checked) {
        document.body.style.fontFamily = serifFonts;
        searchBox.style.fontFamily = serifFonts
        searchButton.style.fontFamily = serifFonts
    } else {
        document.body.style.fontFamily = sansFonts;
        searchBox.style.fontFamily = sansFonts
        searchButton.style.fontFamily = sansFonts
    }

} 


//// niggahita

function niggahitaUp(element) {
    element.innerHTML = element.innerHTML.replace(/ṃ/g, "ṁ");
}

function niggahitaDown(element) {
    element.innerHTML = element.innerHTML.replace(/ṁ/g, "ṃ");
}

niggahitaToggle.addEventListener("change", function() {
    if (this.checked) {
        niggahitaUp(dpdPane);
        niggahitaUp(historyPane);
    } else {
        niggahitaDown(dpdPane);
        niggahitaDown(historyPane);

    }
});

//// grammar button closed / open

grammarToggle.addEventListener("change", function() {
    const grammarButtons = document.getElementsByName("grammar-button");
    const grammarDivs = document.getElementsByName("grammar-div");
    if (this.checked) {
        grammarButtons.forEach(button => {
            button.classList.add("active");
        });
        grammarDivs.forEach(div => {
            div.classList.remove("hidden");
        });
    } else {
        grammarButtons.forEach(button => {
            button.classList.remove("active");
        });
        grammarDivs.forEach(div => {
            div.classList.add("hidden");
        });
    }
});

//// examples button toggle

exampleToggle.addEventListener("change", function() {
    const exampleButtons = document.getElementsByName("example-button");
    const exampleDivs = document.getElementsByName("example-div");
    if (this.checked) {
        exampleButtons.forEach(button => {
            button.classList.add("active");
        });
        exampleDivs.forEach(div => {
            div.classList.remove("hidden");
        });
    } else {
        exampleButtons.forEach(button => {
            button.classList.remove("active");
        });
        exampleDivs.forEach(div => {
            div.classList.add("hidden");
        });
    }
});


// //// sbs examples button toggle
// sbsexampleToggle.addEventListener("change", function() {
//     const sbsexampleButtons = document.getElementsByName("sbs-example-button");
//     const sbsexampleDivs = document.getElementsByName("sbs-example-div");
//     if (this.checked) {
//         sbsexampleButtons.forEach(button => {
//             button.classList.add("active");
//         });
//         sbsexampleDivs.forEach(div => {
//             div.classList.remove("hidden");
//         });
//     } else {
//         sbsexampleButtons.forEach(button => {
//             button.classList.remove("active");
//         });
//         sbsexampleDivs.forEach(div => {
//             div.classList.add("hidden");
//         });
//     }
// });

//// summary 

summaryToggle.addEventListener("change", function() {
    showHideSummary()
});

function showHideSummary() {
    if (summaryToggle.checked) {
        summaryResults.style.display = "block";
    } else {
        summaryResults.style.display = "none";
    }
}

//// sandhi ' toggle

sandhiToggle.addEventListener("change", function() {
    showHideSandhi()
});

function showHideSandhi() {
    if (sandhiToggle.checked) {
        dpdResults.innerHTML = dpdResultsContent;
    } else {
        dpdResults.innerHTML = dpdResultsContent.replace(/'/g, "");
        
    }
}

//// text to unicode

searchBox.addEventListener("input", function() {
    let textInput = searchBox.value;
    let convertedText = uniCoder(textInput);
    searchBox.value = convertedText;
});
