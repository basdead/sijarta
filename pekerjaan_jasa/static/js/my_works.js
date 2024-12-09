function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function acceptWork(orderId) {
    try {
        // Parse the ISO datetime string
        const datetime = new Date("2024-12-09T17:11:14+07:00");
        
        // Format time as HH:mm
        const waktuPekerjaan = datetime.getHours().toString().padStart(2, '0') + "." 
                            + datetime.getMinutes().toString().padStart(2, '0');
        
        // Format date as DD/MM/YYYY
        const tanggalPekerjaan = datetime.getDate().toString().padStart(2, '0') + "/" 
                              + (datetime.getMonth() + 1).toString().padStart(2, '0') + "/" 
                              + datetime.getFullYear();

        const response = await fetch('/work/accept/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                order_id: orderId,
                waktu_pekerjaan: waktuPekerjaan,
                tanggal_pekerjaan: tanggalPekerjaan
            })
        });

        const data = await response.json();
        if (data.status === 'success') {
            // Remove the row from the table
            const row = document.querySelector(`tr[data-order-id="${orderId}"]`);
            if (row) {
                row.remove();
            }
            // Optionally show a success message
            alert('Pekerjaan berhasil diterima!');
            // Reload the page to refresh the tables
            window.location.reload();
        } else {
            alert(data.message || 'Terjadi kesalahan saat menerima pekerjaan');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Terjadi kesalahan saat menerima pekerjaan');
    }
}
