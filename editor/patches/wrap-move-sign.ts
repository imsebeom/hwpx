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
    for (const ref of targets) {
      const props = getObjectProperties.call(this, ref);
      setObjectProperties.call(this, ref, {
        horzOffset: props.horzOffset + deltaH * signH,
        vertOffset: props.vertOffset + deltaV * signV,
      });
    }
    this.pictureMoveState.lastPageX = px;
    this.pictureMoveState.lastPageY = py;
    this.pictureMoveState.totalDeltaH += deltaH * signH;
    this.pictureMoveState.totalDeltaV += deltaV * signV;
