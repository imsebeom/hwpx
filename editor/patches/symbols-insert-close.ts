// ==== find ====
    // 최근 문자 저장
    this.addToRecent(this.selectedChar);
    this.updateRecent();
  }
// ==== replace ====
    // 최근 문자 저장
    this.addToRecent(this.selectedChar);
    this.updateRecent();
    // [claude-hwpx symbols-insert-close] 넣기(두 번 누르기 포함) 뒤 대화상자를 닫는다(한/글과 같이, 사용자 요청 2026-10-18). hide 가 편집 영역 포커스를 되돌린다
    this.hide();
  }
