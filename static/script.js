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
        displaySchedule(data);
    } catch (error) {
        console.error('Erreur lors de la récupération des données:', error);
    }
}

// Fonction pour afficher les données récupérées
function displaySchedule(data) {
    const scheduleList = document.getElementById('schedule-list');
    scheduleList.innerHTML = '';
    data.forEach(item => {
        const listItem = document.createElement('li');
        listItem.textContent = `Jour: ${item.weekday}, Heure: ${item.startTime}, Température: ${item.temperature}°C`;
        scheduleList.appendChild(listItem);
    });
}

// Charger les données au chargement de la page
window.onload = fetchSchedule;

// Fonction pour soumettre le formulaire
async function submitSchedule() {
    const weekday = document.getElementById('weekday').value;
    const startHour = document.getElementById('start_h').value;
    const startMinute = document.getElementById('start_m').value;
    const temperature = document.getElementById('target_temp').value;

    const scheduleItem = {
        weekday: weekday,
        startTime: `${startHour}:${startMinute}`,
        temperature: temperature
    };

    try {
        const response = await fetch('/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scheduleItem)
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
