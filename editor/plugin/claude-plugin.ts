// @ts-nocheck
/**
 * rhwp-studio 플러그인 "claude" — 터미널의 Claude 가 보낸 JSON 명령을 studio 가 들고 있는
 * 바로 그 문서에 적용한다. setup.mjs 가 이 파일을 rhwp-studio/src/plugin/ 으로 복사하고
 * main.ts 의 allowlist 에 등록한다.
 *
 * 명령 한 건(op)의 모양:
 *   { m: "PutFieldText", a: ["기안자", "홍길동"] }   HwpCtrl 메서드
 *   { run: "BreakPara" }                            HwpCtrl Run 액션
 *   { doc: "insertText", a: [0, 3, 0, "본문"] }      WASM HwpDocument 메서드
 * doc 인자 중 객체는 JSON 문자열로 바꿔 넘기고, JSON 문자열 반환값은 파싱해 돌려준다.
 * 배치 하나가 트랜잭션 하나이고 undo 1스텝이다.
 */
import { createHwpCtrl } from '../../../npm/hwpctrl-ocx/src/index.mjs';
import { createAdoptDocument, isMutating } from '../../../npm/hwpctrl-ocx/src/adapter.mjs';

// 이름이 이렇게 시작하는 WASM 메서드는 문서를 바꾸지 않는다고 본다.
const READ_DOC = /^(get|search|export|render|is|has|list|find|measure|hitTest|pageCount)/;

function parseMaybe(value) {
  if (typeof value !== 'string') return value;
  const s = value.trim();
  if (!(s.startsWith('{') || s.startsWith('['))) return value;
  try {
    return JSON.parse(s);
  } catch {
    return value;
  }
}

export const claudePlugin = {
  id: 'claude',
  apiVersion: 1,

  activate(host) {
    const lease = host.borrowDocument();
    const ctrl = createHwpCtrl({
      wasm: null,
      doc: lease ? lease.handle : null,
      adoptDocument: createAdoptDocument(host),
      onSave: (bytes, fileName) => ({ bytes, fileName }),
    });
    host.onDocumentSwap((next) => { ctrl.setDocument?.(next.handle); });

    const mutating = (op) => {
      if (op.m) return isMutating(op.m);
      if (op.doc) return !READ_DOC.test(op.doc);
      return Boolean(op.run);
    };

    const step = (doc, op, i) => {
      try {
        if (op.m) {
          const fn = ctrl[op.m];
          if (typeof fn !== 'function') throw new Error(`HwpCtrl 에 없는 메서드: ${op.m}`);
          return fn.apply(ctrl, op.a || []);
        }
        if (op.run) return ctrl.Run(op.run);
        if (op.doc) {
          const fn = doc[op.doc];
          if (typeof fn !== 'function') throw new Error(`HwpDocument 에 없는 메서드: ${op.doc}`);
          const args = (op.a || []).map((x) => (x !== null && typeof x === 'object' ? JSON.stringify(x) : x));
          return parseMaybe(fn.apply(doc, args));
        }
        throw new Error('op 에 m, run, doc 중 하나가 있어야 한다');
      } catch (e) {
        const err = new Error(`op[${i}] ${JSON.stringify(op).slice(0, 200)} 실패: ${e?.message ?? e}`);
        err.code = 'OP_FAILED';
        throw err;
      }
    };

    return {
      run(ops) {
        const list = Array.isArray(ops) ? ops : [ops];
        if (!list.some(mutating)) return host.read((doc) => list.map((op, i) => step(doc, op, i)));
        return host.transaction(`claude:run(${list.length})`, (tx) => {
          tx.deferPagination();
          const doc = tx.doc();
          return list.map((op, i) => step(doc, op, i));
        });
      },
    };
  },
};

export default claudePlugin;
