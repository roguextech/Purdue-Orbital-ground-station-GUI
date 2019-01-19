#!/bin/bash
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

traceback_path='logs/traceback.log'
program_path='src/ThreadedWindow.py'

ascii="                              
                              
   :;;\`                       
   ;  ,;                      
   .    ;\`                    
    \`    ;.                   
    :     :,                  
     \`     ,:                 
     ,      ,:                
      ,      ,;;;;;\`          
             ;;\`  :;,         
       ,    ;;     :;         
        ,   ;\`  :.  ;,        
         \` \`;    ;\` ;;        
         \` \`;    \`; ;:        
          , ;,    .;;.        
           ::;     ;;         
            ,;;:.,;;;.        
             ..;;;: \`;        
              \`      :;       
               \`      ;,      
               \`\`     .;      
                \`\`     ;;     
                  .    .;\`    
                   :    ;;    
                    ;   ;;\`   
                     ::\`;;:   
                      \`;;;;   
                        .;,   
                              
"

printf "${YELLOW}$ascii\n\n\n"
printf "${NC}PURDUE ORBITAL, ${YELLOW}PURDUE UNIVERSITY\n"
printf "${NC}Ground Station Sub Team\n"
printf "Checking Python version...\n"


version=$( python3 -c 'import sys; print(sys.version_info[1])' )
if [[ ${version} -lt '5' ]]; then
	printf "${RED}[ERROR] Python version must be 3.5 or higher\n"
	printf "Your version is:${NC}\n"
	python3 --version
	printf "${RED}[Process Failed]\n"
	exit 99
fi

printf "Python check passed\n"

printf "Attempting to run ${program_path}\n\n"

python3 ${program_path} 2> ${traceback_path}
if [[ $? == '1' ]]; then
	tail -1 ${traceback_path}
	printf "${RED}^^^^^^^^^^^^\n"
	printf "[ERROR] ${program_path} was unable to start.\n"
	printf "If the underlined error shows ${YELLOW}ImportError${RED}, run ${YELLOW}./setup.sh ${RED}to ensure the proper environment has been set up.\n"
	printf "See ${YELLOW}${traceback_path} ${RED}for the full error stack.\n"
	printf "[Process Failed]\n"
	exit 99
fi

