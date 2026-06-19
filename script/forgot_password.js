
      const form = document.getElementById('forgotForm');
      const toast = document.getElementById('toast');

      function showToast(message, duration = 2600) {
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), duration);
      }

      form.addEventListener('submit', function (e) {
        e.preventDefault();

        const email = document.getElementById('email').value.trim();

        if (!email) {
          showToast('Email wajib diisi.');
          return;
        }

        if (!email.includes('@') || !email.includes('.')) {
          showToast('Format email tidak valid.');
          return;
        }

        showToast('Tautan reset password berhasil dikirim.');
        form.reset();
      });