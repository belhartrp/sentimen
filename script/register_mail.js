
    const loginTab = document.getElementById("loginTab");
    const registerTab = document.getElementById("registerTab");
    const loginBox = document.getElementById("loginBox");
    const registerBox = document.getElementById("registerBox");
    const panelTitle = document.getElementById("panelTitle");
    const panelDesc = document.getElementById("panelDesc");
    const toast = document.getElementById("toast");
    const forgotButton = document.getElementById("forgotButton");
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    function showToast(message, duration = 2400) {
      toast.textContent = message;
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), duration);
    }

    function setMode(mode) {
      const isLogin = mode === "login";

      loginTab.classList.toggle("active", isLogin);
      registerTab.classList.toggle("active", !isLogin);
      loginBox.classList.toggle("active", isLogin);
      registerBox.classList.toggle("active", !isLogin);

      panelTitle.textContent = isLogin ? "Masuk ke akun Anda" : "Buat akun Anda";
      panelDesc.textContent = isLogin
        ? "Gunakan email dan password yang telah terdaftar untuk mengakses sistem."
        : "Buat akun baru menggunakan email dan password untuk mulai mengakses sistem.";
    }

    loginTab.addEventListener("click", () => setMode("login"));
    registerTab.addEventListener("click", () => setMode("register"));

    forgotButton.addEventListener("click", () => {
      const email = document.getElementById("loginEmail").value.trim();

      if (!email) {
        showToast("Masukkan email terlebih dahulu untuk reset password.");
        return;
      }

      showToast("Instruksi reset password dikirim ke email.");
    });

    loginForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value.trim();

      if (!email || !password) {
        showToast("Email dan password wajib diisi.");
        return;
      }

      showToast("Login berhasil.");
      setTimeout(() => {
        window.location.href = "analisis_dataset.html";
      }, 900);
    });

    registerForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const email = document.getElementById("registerEmail").value.trim();
      const password = document.getElementById("registerPassword").value.trim();
      const agreement = document.getElementById("agreement").checked;

      if (!email || !password) {
        showToast("Email dan password wajib diisi.");
        return;
      }

      if (!email.includes("@") || !email.includes(".")) {
        showToast("Format email tidak valid.");
        return;
      }

      if (password.length < 6) {
        showToast("Password minimal 6 karakter.");
        return;
      }

      if (!agreement) {
        showToast("Silakan setujui persyaratan terlebih dahulu.");
        return;
      }

      showToast("Pendaftaran berhasil. Silakan masuk.");
      registerForm.reset();

      setTimeout(() => {
        setMode("login");
        document.getElementById("loginEmail").value = email;
        document.getElementById("loginPassword").focus();
      }, 900);
    });