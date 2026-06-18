document.addEventListener('DOMContentLoaded', function () {
  // Dark mode
  const themeToggle = document.getElementById('themeToggle');
  const savedTheme = localStorage.getItem('medcare-theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  if (themeToggle) {
    themeToggle.innerHTML = savedTheme === 'dark'
      ? '<i class="bi bi-sun"></i>'
      : '<i class="bi bi-moon"></i>';
    themeToggle.addEventListener('click', function () {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('medcare-theme', next);
      themeToggle.innerHTML = next === 'dark'
        ? '<i class="bi bi-sun"></i>'
        : '<i class="bi bi-moon"></i>';
    });
  }

  // Mobile sidebar
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('show'));
  }

  // Appointment slot loader
  const doctorSelect = document.getElementById('id_doctor');
  const dateInput = document.getElementById('id_date');
  const timeInput = document.getElementById('id_time');
  const slotsContainer = document.getElementById('available-slots');

  function loadSlots() {
    if (!doctorSelect || !dateInput || !slotsContainer) return;
    const doctorId = doctorSelect.value;
    const date = dateInput.value;
    if (!doctorId || !date) {
      slotsContainer.innerHTML = '<p class="text-muted small mb-0">Select doctor and date to see available slots.</p>';
      return;
    }
    fetch(`/appointments/api/slots/?doctor_id=${doctorId}&date=${date}`)
      .then(r => r.json())
      .then(data => {
        if (!data.slots.length) {
          slotsContainer.innerHTML = '<p class="text-muted small mb-0">No available slots for this date.</p>';
          return;
        }
        slotsContainer.innerHTML = data.slots.map(slot =>
          `<button type="button" class="btn btn-sm btn-outline-primary me-1 mb-1 slot-btn" data-slot="${slot}">${slot}</button>`
        ).join('');
        document.querySelectorAll('.slot-btn').forEach(btn => {
          btn.addEventListener('click', function () {
            if (timeInput) timeInput.value = this.dataset.slot;
            document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
          });
        });
      });
  }

  if (doctorSelect) doctorSelect.addEventListener('change', loadSlots);
  if (dateInput) dateInput.addEventListener('change', loadSlots);

  // Auto-dismiss toasts
  document.querySelectorAll('.toast').forEach(toast => {
    setTimeout(() => {
      const bsToast = bootstrap.Toast.getOrCreateInstance(toast);
      bsToast.hide();
    }, 5000);
  });
});
