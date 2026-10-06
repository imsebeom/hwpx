// ==== find ====
        self.claude_init_measure_offsets();
        let mut targets = Vec::new();
// ==== replace ====
        self.claude_init_measure_offsets();
        let mut targets = Vec::new();
        // [claude-hwpx nested-sync-nontac] 글자처럼 취급이 아닌 본문 표(문항카드의 쪽 크기 상자) 안의 글자처럼 취급 표 속 표
        let mut nested_only = Vec::new();
// ==== next ====
                        if t.dirty && t.common.treat_as_char {
                            targets.push((si, pi, ci));
                        }
// ==== replace ====
                        if t.dirty && t.common.treat_as_char {
                            targets.push((si, pi, ci));
                        } else if t.dirty {
                            // 바깥 표가 글자처럼 취급이 아니면 쪽 나누기 맞춤 대상이 아니지만, 그 안의 글자처럼 취급 표 속 표는
                            // 편집 뒤 높이를 다시 재야 한다. 종전에는 안쪽 표가 옛 높이로 남아 글을 지우거나 그림을 줄여도 상자가 안 줄었다
                            nested_only.push((si, pi, ci));
                        }
// ==== next ====
            self.claude_sync_nested_tac(si, pi, ci);
            self.sync_tac_table_host_line(si, pi, ci);
        }
    }
// ==== replace ====
            self.claude_sync_nested_tac(si, pi, ci);
            self.sync_tac_table_host_line(si, pi, ci);
        }
        for (si, pi, ci) in nested_only {
            self.claude_sync_nested_tac(si, pi, ci);
        }
    }
