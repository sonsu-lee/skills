# Personal Skills

직접 만든 스킬을 플러그인으로 배포하고, 외부 스킬의 출처와 설치 구성을 관리하는 개인 저장소입니다.

## 구조

- `skills/`: 직접 만든 스킬을 보관합니다.
- `catalog/`: 외부 스킬을 소스 복사 없이 분류하고 설치 방법을 기록합니다.
- `docs/DESIGN.md`: 저장소의 현재 설계와 작업 원칙을 기록합니다.

직접 만든 스킬은 아직 없습니다. 외부 카탈로그에는 검토한 초기 profile과 add-on만 등록되어 있으며, 소스는 포함하지 않습니다.

## 외부 스킬

외부 프로젝트는 이 저장소에 복사하거나 미러링하지 않습니다. 설치할 때 upstream 저장소, `npx skills` 또는 호스트의 공식 플러그인을 사용합니다.

자세한 경계와 설치 방향은 [`docs/DESIGN.md`](docs/DESIGN.md), 등록 원칙은 [`catalog/README.md`](catalog/README.md)를 참고하세요.
