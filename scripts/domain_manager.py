#!/usr/bin/env python3
"""
Domain Manager - Utility script to manage domain configurations
Allows users to easily enable/disable domains and view current settings
"""

import GameConfig

def print_domain_status():
    """Print the current status of all domains"""
    print("\n" + "="*60)
    print("           DOMAIN CONFIGURATION STATUS")
    print("="*60)
    
    enabled_count = 0
    for domain_key, config in GameConfig.DOMAIN_CONFIG.items():
        status = "✅ ENABLED" if config["enabled"] else "❌ DISABLED"
        print(f"{config['name']:<25} | {status}")
        if config["enabled"]:
            enabled_count += 1
    
    print("-"*60)
    print(f"Total Domains: {len(GameConfig.DOMAIN_CONFIG)}")
    print(f"Enabled: {enabled_count}")
    print(f"Disabled: {len(GameConfig.DOMAIN_CONFIG) - enabled_count}")
    print("="*60)

def enable_domain(domain_name):
    """Enable a specific domain"""
    if GameConfig.set_domain_enabled(domain_name, True):
        print(f"✅ Enabled domain: {domain_name}")
    else:
        print(f"❌ Domain not found: {domain_name}")

def disable_domain(domain_name):
    """Disable a specific domain"""
    if GameConfig.set_domain_enabled(domain_name, False):
        print(f"✅ Disabled domain: {domain_name}")
    else:
        print(f"❌ Domain not found: {domain_name}")

def get_available_domains():
    """Get list of all available domain names"""
    return GameConfig.get_all_domain_names()

def interactive_menu():
    """Interactive menu for domain management"""
    while True:
        print("\n" + "="*50)
        print("           DOMAIN MANAGER")
        print("="*50)
        print("1. View current domain status")
        print("2. Enable a domain")
        print("3. Disable a domain")
        print("4. List all available domains")
        print("5. Exit")
        print("-"*50)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            print_domain_status()
        
        elif choice == "2":
            print("\nAvailable domains to enable:")
            all_domains = get_available_domains()
            for i, domain in enumerate(all_domains, 1):
                status = "✅" if GameConfig.is_domain_enabled(domain) else "❌"
                print(f"{i}. {domain} {status}")
            
            try:
                domain_num = int(input("\nEnter domain number to enable: ")) - 1
                if 0 <= domain_num < len(all_domains):
                    enable_domain(all_domains[domain_num])
                else:
                    print("❌ Invalid domain number!")
            except ValueError:
                print("❌ Please enter a valid number!")
        
        elif choice == "3":
            print("\nEnabled domains to disable:")
            enabled_domains = GameConfig.get_enabled_domains()
            if not enabled_domains:
                print("No domains are currently enabled.")
                continue
            
            for i, domain_name in enumerate(enabled_domains.keys(), 1):
                print(f"{i}. {domain_name}")
            
            try:
                domain_num = int(input("\nEnter domain number to disable: ")) - 1
                domain_list = list(enabled_domains.keys())
                if 0 <= domain_num < len(domain_list):
                    disable_domain(domain_list[domain_num])
                else:
                    print("❌ Invalid domain number!")
            except ValueError:
                print("❌ Please enter a valid number!")
        
        elif choice == "4":
            print("\nAll available domains:")
            all_domains = get_available_domains()
            for i, domain in enumerate(all_domains, 1):
                status = "✅" if GameConfig.is_domain_enabled(domain) else "❌"
                print(f"{i}. {domain} {status}")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice! Please enter 1-5.")

def quick_commands():
    """Show quick command examples"""
    print("\n" + "="*50)
    print("           QUICK COMMANDS")
    print("="*50)
    print("To enable a domain programmatically:")
    print("  GameConfig.set_domain_enabled('Equipment Finance', True)")
    print("\nTo disable a domain programmatically:")
    print("  GameConfig.set_domain_enabled('Lending', False)")
    print("\nTo get enabled domains:")
    print("  enabled = GameConfig.get_enabled_domains()")
    print("\nTo check if a domain is enabled:")
    print("  is_enabled = GameConfig.is_domain_enabled('Trade Finance')")
    print("="*50)

if __name__ == "__main__":
    print("🎮 Maze Runner Domain Manager")
    print("This utility helps you manage which domains appear in the game.")
    
    # Show current status
    print_domain_status()
    
    # Show quick commands
    quick_commands()
    
    # Start interactive menu
    interactive_menu() 