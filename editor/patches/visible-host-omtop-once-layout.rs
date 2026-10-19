// ==== find ====
                        Some(para_y_for_table + visible_outer_top_px),
// ==== replace ====
                        // [claude-hwpx visible-host-omtop-once] HWPX 는 compute_table_y_position 이 바깥 위 여백을 더한다(para-tbl-omtop)
                        Some(
                            para_y_for_table
                                + if self.profile.get().hwpx_container() {
                                    0.0
                                } else {
                                    visible_outer_top_px
                                },
                        ),
