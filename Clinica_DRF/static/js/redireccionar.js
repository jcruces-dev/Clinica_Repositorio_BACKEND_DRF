document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        // Una vez ingresada a la página de confirmacion reserva, redirigimos al usuario a la página de inicio después de 2 segundos.
        window.location.href = "http://127.0.0.1:5500/Clinica_HTML/index.html"; 
        // 2000 milisegundos = 2 segundos
    }, 2000);
});