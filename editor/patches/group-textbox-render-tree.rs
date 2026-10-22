// ==== find ====
    /// [Task #1138] 표 셀 내 도형인 경우: outer paragraph 의 표 control 인덱스
    #[serde(default)]
    pub outer_table_control_index: Option<usize>,
}

impl RectangleNode {
// ==== replace ====
    /// [Task #1138] 표 셀 내 도형인 경우: outer paragraph 의 표 control 인덱스
    #[serde(default)]
    pub outer_table_control_index: Option<usize>,
    /// [claude-hwpx group-textbox] 묶음 자식이면 글상자 셀 경로 칸 번호(묶음 자식 경로), 아니면 0
    #[serde(skip)]
    pub claude_group_code: usize,
}

impl RectangleNode {
// ==== next ====
            cell_index: None,
            cell_para_index: None,
            outer_table_control_index: None,
        }
    }
}

/// 타원 노드
// ==== replace ====
            cell_index: None,
            cell_para_index: None,
            outer_table_control_index: None,
            claude_group_code: 0, // [claude-hwpx group-textbox]
        }
    }
}

/// 타원 노드
