// Fonction pour récupérer et afficher les données de l'URI /schedule
async function fetchSchedule() {
    try {
        const response = await fetch('/schedule', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        displaySchedules(data);
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error);
    }
}

// Fonction pour afficher les données récupérées dans les onglets correspondants
function displaySchedules(data) {
    const days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
    days.forEach((day, index) => {
        const scheduleList = document.getElementById(`schedule-list-${index}`);
        if (scheduleList) {
            scheduleList.innerHTML = '';
            data.forEach(item => {
                if (item.weekday === index) {
                    const listItem = document.createElement('li');
                    listItem.textContent = `Heure: ${formatTime(item.start_h, item.start_m)}, Température: ${item.target_temp}°C`;
                    scheduleList.appendChild(listItem);
                }
            });
        }
    });
}

// Fonction pour obtenir le nom du jour à partir de la valeur
function getDayName(weekday) {
    const days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
    return days[weekday];
}

// Fonction pour formater l'heure
function formatTime(hours, minutes) {
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

// Fonction pour ouvrir un onglet spécifique
function openTab(evt, dayName) {
    const tabcontent = document.getElementsByClassName("tabcontent");
    for (let i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }

    const tablinks = document.getElementsByClassName("tablinks");
    for (let i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    const tabToShow = document.getElementById(dayName);
    if (tabToShow) {
        tabToShow.style.display = "block";
        evt.currentTarget.className += " active";
    }
}

// Charger les données au chargement de la page et ouvrir l'onglet Lundi par défaut
window.onload = function() {
    fetchSchedule();
    const lundiTab = document.getElementById('Lundi');
    const firstTabLink = document.querySelector('.tablinks');
    if (lundiTab && firstTabLink) {
        lundiTab.style.display = 'block';
        firstTabLink.classList.add('active');
    }
}

// Fonction pour soumettre le formulaire
async function submitSchedule() {
    const weekday = document.getElementById('weekday').value;
    const startHour = document.getElementById('start_h').value;
    const startMinute = document.getElementById('start_m').value;
    const temperature = document.getElementById('target_temp').value;

    const scheduleItem = {
        weekday: parseInt(weekday),
        start_h: parseInt(startHour),
        start_m: parseInt(startMinute),
        target_temp: parseFloat(temperature)
    };

    try {
        const response = await fetch('/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify([scheduleItem])
        });

        if (response.ok) {
            fetchSchedule(); // Recharger la liste après l'ajout
        } else {
            console.error('Erreur lors de l\'ajout de la planification:', response.statusText);
        }
    } catch (error) {
        console.error('Erreur lors de l\'ajout de la planification:', error);
    }
}
