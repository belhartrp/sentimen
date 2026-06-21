
    const form = document.getElementById("resetForm");
    const toast = document.getElementById("toast");

    function showToast(message, duration = 2600){
      toast.textContent = message;
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), duration);
    }

    form.addEventListener("submit", function(e){
      e.preventDefault();

      const newPassword = document.getElementById("newPassword").value.trim();
      const confirmPassword = document.getElementById("confirmPassword").value.trim();

      if (!newPassword || !confirmPassword){
        showToast("Semua field wajib diisi.");
        return;
      }

      if (newPassword.length < 6){
        showToast("Password minimal 6 karakter.");
        return;
      }

      if (newPassword !== confirmPassword){
        showToast("Konfirmasi password tidak sama.");
        return;
      }

      showToast("Password berhasil diperbarui.");

      setTimeout(() => {
        window.location.href = "register.html";
      }, 1200);
    });
  