// Add this to static/js/sending_status.js
function updateSendingStatus(){
    fetch('/status/sending').then(r => r.json()).then(data => {
        const el = document.getElementById('sending-status');
        if(data.active){
            el.textContent = 'Sending: ' + (data.progress || 'In progress...');
            el.className = 'badge connected';
        } else if(data.progress) {
            el.textContent = 'Sending: ' + data.progress;
            el.className = 'badge';
        } else {
            el.textContent = '';
            el.className = 'badge';
        }
    }).catch(err => {
        const el = document.getElementById('sending-status');
        el.textContent = 'Sending: Error';
        el.className = 'badge disconnected';
    });
}
document.addEventListener('DOMContentLoaded', function(){
    setInterval(updateSendingStatus, 2000);
});
