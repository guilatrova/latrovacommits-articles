---
tags: [DevOps, Ubuntu, Productivity, ansible]
---

# Como um DevOps você deveria estar fazendo seus backups assim

Como um engenheiro DevOps, não há nada que eu não faça hoje que eu não considere como automatizar pra ser mais rápido e produtivo.
Recentemente eu percebi quão repetitivo eram os passos que eu tomava sempre que formatava o computador, que são basicamente:

1. Realizar backup de dados e configurações
2. (Re)instalar novo OS
3. Restaurar meu backup
4. Restaurar cada pequena configuração e instalação

Já que o Ubuntu 19.10 já está disponível (Eu estive usando o 18.04 por um bom tempo), finalmente achei um tempo para experimentá-lo.

A principal razão pra tentar automatizar esse processo é deixar fácil a migração entre as versões do linux e voltar a trabalhar rápido sem ter que gastar todo o final de semana deixando tudo em ordem.

Então vou mostrar como o Ansible pode te ajudar a resolver essas questões. Com sorte, espero que isso te dê alguns insights sobre a importância da cultura DevOps dentro de toda empresa que deseja aumentar sua produtividade.

Se você estiver curioso pra ver o resultado final, já está disponível em: [https://github.com/guilatrova/base-dev-setup/](https://github.com/guilatrova/base-dev-setup/)

## Por que Ansible?

Nós vamos ter vários passos que poderão ser re-executados várias e várias vezes (tanto pra backup quanto pra atualizar alguma ferramenta), e os playbooks atendem esse requisito perfeitamente.

Em seu site oficial, eles alegam que:
> Ansible is a universal language, unraveling the mystery of how work gets done. Turn tough tasks into repeatable playbooks. Roll out enterprise-wide protocols with the push of a button.


## Backup com 1 comando

Regras que este playbook deve seguir:

**1. O backup tem que ser feito na nuvem**

Não quero me preocupar de ter espaço disponível nos meus pen drives, nem ficar carregando eles por aí. Eu gosto de ter meus dados disponíveis de qualquer lugar. Eu decidi usar o AWS S3 pra atender esse requisito.

**2. Customizável**

Deve ser fácil de adicionar e remover pastas do meu backup. Eu escolhi definir uma lista de váriaveis da maneira mais fácil e simples possível:

```yaml
{
    remote: PASTA_NUVEM,
    local: PASTA_LOCAL
}
```

**3. Fácil de executar**

Tem que ser possível executar o mesmo comando milhares de vezes sem enrolação, e nesse caso o comando será: `ansible-playbook playbooks/backup.yml`.

### Resultado

É tudo tão fácil com Ansible, já temos disponível o módulo que nos ajuda a fazer o backup: `s3_sync` [https://github.com/guilatrova/base-dev-setup/blob/master/roles/backup/tasks/main.yml](https://github.com/guilatrova/base-dev-setup/blob/master/roles/backup/tasks/main.yml)

Fica fácil também filtrar arquivos (ao invés de enviar uma pasta inteira pra nuvem): [https://github.com/guilatrova/base-dev-setup/blob/master/vars/backup.example.yml](https://github.com/guilatrova/base-dev-setup/blob/master/vars/backup.example.yml)

Eu fiz o meu melhor pra realizar o backup dos meus atalhos de teclado no Ubuntu. Infelizmente, não consegui fazer funcionar.
Fique a vontade pra criar uma PR se você tiver uma solução 😃.

## Restaurando todos os meus dados

Bom, somente realizar o backup e não poder restaurá-los na mesma velocidade me parece falho. Por isso o playbook de restauração deve seguir a mesma lógica com alguns detalhes extras:

**1. Arquivos restaurados devem voltar pro seu local original**

Eu não quero ficar recortando e colando arquivos. Se eu tiver que fazer qualquer passo manualmente, o processo não é bom o bastante.

**2. Cuidar de casos onde os arquivos são localizados em diretórios protegidos**

Existem alguns arquivos, binários e scripts que ficam localizados em: `/usr/local/bin`, mas esse diretório tem proteção contra escrita por padrão. Ainda quero manter a ferramenta simples e fácil de usar, as variáveis devem tratar uma possível opção `sudo: true`.

**3. Pacotes e binários devem ser instalados ou atualizados**

Não quero instalar o Slack de novo. Cara, eu realmente amo configurar meu VSCodium, mas toda hora?
Como meu computador é minha ferramente de trabalho, eu preciso dele pronto o mais rápido possível pra manter meu trabalho fluindo.

Então, esse playbook deve cuidar da instalação (e updates claro!) de todas minhas ferramentas de trabalho.

Veja a lista de algumas ferramentas/binários que ele instala:

- git
- docker
- vscodium
- mysqlcli
- dbeaver
- npm
- circleci
- slack
- zoom
- terraform
- kubectl
- aws-iam-authenticator
- shellcheck
- tilda
- wtfutil
- moo.do
- tusk
- spotify
- postman
- gitkraken

Alguns deles podem soar meio novo pra vocês, vou apresentar  alguns como bônus ao final deste artigo 😃

Tem mais algumas ferramentas, fique a vontade pra explorar a [task](https://github.com/guilatrova/base-dev-setup/blob/master/roles/packages/tasks/main.yml) você mesmo.

Foi pensado pra ser fácil de remover/substituir ferramentes, então se você não quiser instalar o CLI do CircleCI, por exemplo, você pode simplesmente deletar as seguintes linhas:

```yaml
- import_tasks: dev/circleci.yml
  tags: circleci, binaries, dev
```

A mesma ideia se aplica se você estiver atualizando/reinstalando alguma ferramenta. Você deve poder filtrá-las por tags.

**4. Repositórios devem ser clonados novamente**

Atualmente eu trabalho em uma empresa que segue uma arquitetura de microserviços. Em outras palavras, eu tenho vários "micro" repositório para propósitos específicos. Eu odeio quando eu tento abrir um repositório que eu esqueci de clonar na minha máquina.

É por esse motivo que o passo final de todo o processo é clonar todos os repositórios que eu estou usando.

Eu os dividi em 2 grupos "personal" (pessoal) e "company" (empresa), então você pode clonar esses grupos em diferentes pastas se quiser.

A mesma regra do "fácil de customizar" se aplica aqui, você tem variáveis onde você pode especificar uma lista de repositórios e então o Ansible fará tudo por você:

```yaml
company_org: "my-company-org"
company_repo_dest: "{{ home_folder }}/my-company/"
company_repos:
  - "my-company-repo"
  - "my-second-company-repo"
```
## O que mais posso fazer com Ansible?

Como você já deve ter notado, Ansible pode automatizar **praticamente tudo**. Se sua empresa não usa nenhuma ferramenta de automação, comece agora mesmo a notar que processos repetitivos seu time faz toda semana.
Desde backups (conforme mostrado neste artigo) a [adicionar novos membros e gerenciar permissões no AWS](https://docs.ansible.com/ansible/latest/modules/iam_module.html), o Ansible pode te ajudar!

Em um século onde empresas e startups estão desejando entregar cada vez mais e chegar ao mercado mais rápido, nós precisamos descobrir formas de fazer menos e ainda entregar mais.

O mais cedo sua empresa perceber quanto tempo pode economizar automatizando tarefas repetitivas, o mais cedo esse tempo vai ser alocado para tarefas que produzam valor para os engenheiros.

## 🚀 Bônus: Sugestão de ferramentas para aumentar sua produtividade e privacidade

Você deve ter notado algumas ferramentas diferentes, como [VSCodium](https://vscodium.com/) (ao invés do VSCode) e [Moo.do](https://www.moo.do/).

Deixe-me te apresentar algumas ferramentas (e o motivo pelo) que serão úteis pra você.

#### VSCodium

Nada mais é do que o _VSCode sem binários da Microsoft_. Diretamente da página deles:

> Microsoft’s vscode source code is open source (MIT-licensed), but the product available for download (Visual Studio Code) is licensed under this not-FLOSS license and contains telemetry/tracking. According to this comment from a Visual Studio Code maintainer: [...]

#### Shellcheck

**É OBRIGATÓRIO para qualquer desenvolvedor que crie scripts em bash** de tempos em tempos. Ele valida seu código e te ajuda a evitar alguns problemas bem conhecidos.

#### wtfutil

Apesar do nome engraçado, essa ferramenta é muito útil (Eu gosto de rodar ela no Tilda) e me mantém atualizado sobre as últimas [Hacker News](https://news.ycombinator.com) enquanto me lembra das minhas tarefas do Jira.

![wtfutil running in tilda](wtfutil.png)

#### Moo.do

Essa é minha ferramenta favorita que me ajuda a focar no que realmente importa, ainda me oferece controle dos meus e-mail e eventos da agenda. É extramente fácil de usar, e você pode adicionar uma tarefa na genda, ou transformar um e-mail em uma tarefa e daí em diante.
