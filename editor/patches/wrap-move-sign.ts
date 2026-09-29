// ==== find ====
  if (deltaH === 0 && deltaV === 0) return;

  try {
    // 다중 선택: 모든 개체를 동일 delta로 이동
    const targets = this.pictureMoveState.multiRefs || [this.pictureMoveState.ref];
    for (const ref of targets) {
      const props = getObjectProperties.call(this, ref);
      setObjectProperties.call(this, ref, {
        horzOffset: props.horzOffset + deltaH,
        vertOffset: props.vertOffset + deltaV,
      });
    }
    this.pictureMoveState.lastPageX = px;
    this.pictureMoveState.lastPageY = py;
    this.pictureMoveState.totalDeltaH += deltaH;
    this.pictureMoveState.totalDeltaV += deltaV;
// ==== replace ====
  if (deltaH === 0 && deltaV === 0) return;

  try {
    // 다중 선택: 모든 개체를 동일 delta로 이동
    const targets = this.pictureMoveState.multiRefs || [this.pictureMoveState.ref];
    // [claude-hwpx wrap-move-sign] 오른쪽(바깥쪽) 정렬 개체의 가로 거리는 오른쪽 끝에서 안쪽으로, 아래(바깥쪽) 정렬은
    // 아래 끝에서 위로 잰다. 마우스 이동량을 그대로 더하면 끄는 방향과 반대로 움직였다(2026-09-29 사용자 발견).
    // 한 개를 고른 경우만 부호를 맞춘다 — 여러 개는 되돌리기 기록이 이동량 하나를 함께 쓴다
    let signH = 1;
    let signV = 1;
    if (!this.pictureMoveState.multiRefs) {
      const p0 = getObjectProperties.call(this, targets[0]);
      if (p0.horzAlign === 'Right' || p0.horzAlign === 'Outside') signH = -1;
      if (p0.vertAlign === 'Bottom' || p0.vertAlign === 'Outside') signV = -1;
    }
    // 한글은 문단 기준 개체의 음수 세로 거리를 0 으로 눌러 그린다(한글 PDF 실측 7건) — 끄는 동안 0 아래로 내려가지 않게 한다.
    // 실제로 바뀐 만큼만 쌓아 되돌리기 기록과 맞춘다
    let appliedV = deltaV * signV;
    for (const ref of targets) {
      const props = getObjectProperties.call(this, ref);
      let nextV = props.vertOffset + deltaV * signV;
      if (!this.pictureMoveState.multiRefs && props.vertRelTo === 'Para' && nextV < 0) nextV = 0;
      if (!this.pictureMoveState.multiRefs) appliedV = nextV - props.vertOffset;
      setObjectProperties.call(this, ref, {
        horzOffset: props.horzOffset + deltaH * signH,
        vertOffset: nextV,
      });
    }
    this.pictureMoveState.lastPageX = px;
    this.pictureMoveState.lastPageY = py;
    this.pictureMoveState.totalDeltaH += deltaH * signH;
    this.pictureMoveState.totalDeltaV += appliedV;
