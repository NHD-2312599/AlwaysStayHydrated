(function () {
  function dateKey(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  function updateMissionProgress(mode, amount = 1, metric = '') {
    const key = `missions_${dateKey(new Date())}`;
    let data;
    try {
      data = JSON.parse(localStorage.getItem(key) || 'null');
    } catch (error) {
      return false;
    }
    if (!data || data.version !== 2 || !Array.isArray(data.required) || !Array.isArray(data.optional)) return false;

    let changed = false;
    [...data.required, ...data.optional].forEach(mission => {
      const isDone = mission.done || mission.progress >= mission.target;
      if (mission.mode !== mode || (metric && mission.metric !== metric) || isDone) return;
      mission.progress = Math.min(mission.target, (mission.progress || 0) + amount);
      mission.done = mission.progress >= mission.target;
      changed = true;
    });
    if (!changed) return false;

    localStorage.setItem(key, JSON.stringify(data));
    localStorage.setItem(`activity_${dateKey(new Date())}`, '1');
    window.dispatchEvent(new CustomEvent('missionprogresschange'));
    return true;
  }

  window.updateMissionProgress = window.updateMissionProgress || updateMissionProgress;
}());
